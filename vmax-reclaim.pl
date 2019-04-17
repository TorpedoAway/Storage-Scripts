#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Long;
use POSIX;
use Data::Dumper;
use JSON qw( );
use XML::Simple;



=pod

=head1 DESCRIPTION

This script has several mandatory parameters, (--sid, --chg,  --tdev, --sg )

This is the Storage Ops VMAX LUN reclaim script. It performs reclaim and audits the
reclaim for tracking purposes.

=head1 USAGE

./vmax-reclaim.pl  --sid <Sym SID#> --chg <CHGxxxx> --tdev <LUN ID> --sg <SG NAme>


 --chg       Service Now Change number
 --tdev     Integer number of LUNs to be created of the size specified by --gb.
 --sg        Name of the SG to receive the LUN(s)
 --sid       SID of array used for allocation.
 --dryrun    Optional parameter. Just print out the symconfigure command.

=head1 Examples

  ./vmax-reclaim.pl   --sid 1234 --chg CHG123456 --tdev xxxx  --sg tf_test_S
  ./vmax-reclaim.pl   --sid 1234 --chg CHG123457 --tdev xxxx  --sg tf_test_S
  ./vmax-reclaim.pl   --sid 1234 --chg CHG000000 --tdev "0267,0269,026B,026D" --sg tf_test_S

=head1 Logs

  Reclaime are recorded and sent to the Storage Ops Reporting Server.
  Commands are logged to the following logfile on the CLI host where
  vmax-reclaim is executed.

  /usr/local/StorageOps/logs/reclaim.log

=head1 Notes

  If all the inputs are validated the script will run symaccess to reclaim the LUNs.
  All output will be captured and logged. If the symaccess fails, the scripts will
  exit with an appropriate error. If the symaccess succeedes, the script will capture the
  and log the output. It will also format a JSON file to be forwarded to the reporting server.

  Once received by the reporting server the JSON file will be processed and added to a reclaim database.

=head1 Error Checking

  The script does the following error checking:

      1. Verify the SG exists on the target array.
      2. Verify the lun to be reclaimed is in that SG
      3. Check if the lun is the last LUN in the SG and print a warning if so.
      4. Check whether the LUN is mapped to a port. Use -unmap is it is mapped.

=cut


my $LOG = '/usr/local/StorageOps/logs/reclaim.log';
my %auditlog;

check_root();

$ENV{'PATH'} = '/opt/emc/SYMCLI/bin:/usr/bin:/usr/sbin:/usr/local/bin';

my %sgmap;
my %optctl = ();
GetOptions (\%optctl, "sid=i", "chg=s", "tdev=s", "sg=s", "dryrun");


my @RequiredOptions = qw(
    chg
    tdev
    sg
    sid
);

# Verify we have required options
for my $opt (@RequiredOptions) {
    if (! exists($optctl{$opt}) ) {
        usage();
    }
}


my $sg = $optctl{'sg'};
my $sid = $optctl{'sid'};
my $sglunmap = make_lunmap($sg);
check_sg($sid);


my $tdevs = uc $optctl{'tdev'};
my @tdevs = split(/,/,$tdevs);

if ( exists($optctl{'dryrun'}) ) {
    print "Dry run commands...\n";
}

foreach my $tdev (@tdevs) {
    $tdev = format_tdev($tdev);
    reclaim_lun($tdev);
}    

sub reclaim_lun {

    my $tdev = shift;
    
    check_lun($sglunmap,$tdev);
    my $unmap = check_mapped($sid,$tdev);
    my $command = "symaccess -sid  $sid  -type storage -name $sg remove devs $tdev $unmap";

    if ( exists($optctl{'dryrun'}) ) {
        print "$command\n";
    } else {
        write_log($LOG,"Processing CHG - $optctl{'chg'}");
        write_log($LOG,"Running Command - $command");
        print "Running Command - $command\n";
        my ($output,$result) = runcmd($command);
        if ( $result != 0 ) {
            print "$result\n";
            for my $line ( @{$output} ) {
                print "$line\n";
            }
            print "\n\nExiting...\n";
            exit(1);    
        } else {
            print "LUN reclaimed successfully.\n";
        }
        write_log($LOG,"Reclaimed $tdev");
        $auditlog{'chg'} = $optctl{'chg'};
        $auditlog{'sid'} = $optctl{'sid'};
        $auditlog{'sg'} = $optctl{'sg'};
        $auditlog{'lun_ids'} = $tdev;
        $auditlog{'size'} = $sglunmap->{$tdev};
        $auditlog{'date'} = strftime "%m/%d/%Y", localtime;
        my $json_obj = new JSON;
        my $json_text = $json_obj->pretty->encode(\%auditlog);
        my $outputfile = '/usr/local/StorageOps/data/reclaims/' . $optctl{'chg'} . '_' . time . '.json';
        open(my $fh, ">", $outputfile);
        print $fh $json_text;
        print $json_text;

        my $label = "DELETE_" . strftime "%m_%d_%Y" , localtime(time + (60*60*24*7));
        $label .= "_" . $optctl{'chg'};
        my $labelcmd = "symconfigure -sid $sid -cmd \"set dev $tdev device_name=\'$label\';\" commit -nop";
        print "Labeling device for future deletion...\n$labelcmd\n";
        ($output, $result) = runcmd($labelcmd);
        if ( $result != 0 ) {
            print "$result\n";
            for my $line ( @{$output} ) {
                print "$line\n";
            }
        } else {
            print "LUN labeled successfully.\n";
        }
    }

}

sub usage {
    exec("/usr/bin/perldoc $0");
}


sub get_groups {
    my $sid = shift;
    my $command = "symaccess -sid $sid -type storage list -output xml_e|grep group_name";
    open(CMD,"$command|") or die "Failed running command: $command\n($!)\n";
    while (my $line = <CMD>) {
        chomp($line);
        my @fields = split(/\>/,$line);
        my @fields2 = split(/\</,$fields[1]);
        $sgmap{$fields2[0]} = 1;
    }
}

sub runcmd {
    my $command = shift;
    my @out;
    my $outputfile = '/tmp/vmax-reclaim.tmp.' . time;
    my $result = 0;
    system("$command >$outputfile 2>&1") == 0
        or $result =  "$0: symcli exited with return code " . ($? >>8) . "\n";

    open(my $fh, "<", $outputfile);
    while (my $line = <$fh>) {
        chomp($line);
        push @out, $line;
    }
    system("cat $outputfile >> $LOG");
    unlink($outputfile);
    return \@out, $result;
}


sub write_log {
    my $date = localtime(time);
    my($log,$entry) = @_;
    if (! -e $log) {
        open(my $fh, ">", $log);
        print $fh "$date : Begin Log\n";
        close($fh);
    }
    open(my $fh, ">>", $log);
    print $fh "$date : $entry\n";
    close($fh);
}

sub get_xml {
    my $cmd = shift;
    my $xml = '';
    open(SYMCLI,"$cmd|") or die "Failed opening $cmd ($!)\n";
    while (my $line = <SYMCLI>) {
        $xml .= $line;
    }
    return $xml;
}

sub check_root {
    # Require root user
    if ( $> != 0 ) {
        print "\n\nThis script requires root permissions.\n";
        print "Use su or sudo to become root before running this script.\n";
        print "\nExiting...\n";
        exit(1);
    }
}

sub check_sg {
    my $sid = shift;
    get_groups($sid);
    if ( ! exists($sgmap{$sg})) {
        print "ERROR: SG $optctl{'sg'} does not exist. Exiting...\n";
        exit(1);
    }
}


sub format_tdev {
    my $tdev = shift;
    $tdev = '0' . $tdev if (length($tdev) == 3);
    $tdev = '00' . $tdev if (length($tdev) == 2);
    $tdev = '000' . $tdev if (length($tdev) == 1);
    $tdev = substr($tdev, -4);
    return $tdev;
}


sub make_lunmap {
    my $sg = shift;
    my $cmd = "symcfg -sid $sid list -tdev -gb -sg $sg -output xml_e";
    my $xml = get_xml($cmd);
    my $ref = XMLin($xml, ForceArray => 0);

    my %sglunmap;

    if (defined $ref->{Symmetrix}{ThinDevs}{Device}) {
        my $type = $ref->{Symmetrix}{ThinDevs}{Device};
        #print Dumper($ref);
        #print "$type\n";
        if ( $type =~ /array/i) {
            foreach my $device (@{$ref->{Symmetrix}{ThinDevs}{Device}}) {
                #print Dumper($device);
                my $lun = substr($device->{dev_name},-4);
                my $size = $device->{total_tracks_gb};
                $sglunmap{$lun} = $size;
            }
        } elsif ( $type =~ /hash/i) {
            my $lun = substr($ref->{Symmetrix}{ThinDevs}{Device}{dev_name},-4);
            my $size = $ref->{Symmetrix}{ThinDevs}{Device}{total_tracks_gb};
            $sglunmap{$lun} = $size;
        }
    }
    return \%sglunmap;
}


sub check_lun {
    my($sglunmap,$tdev) = @_;
    #print Dumper($sglunmap);
    if (! exists($sglunmap->{$tdev})  ) {
        print "$tdev not found in $sg. Exiting...\n\n";
        exit(1);
    }

    my @luns = keys %{$sglunmap};
    if ($#luns == 0) {
        print "$tdev is the last lun in $sg. \n";
        print "You may have to delete the View before removing this LUN\n";
    }

}


sub check_mapped {
    my ($sid, $tdev) = @_;
    my $cmd = "symdev -sid $sid show $tdev -output xml_e";
    my $xml = get_xml($cmd);
    my $ref = XMLin($xml, ForceArray => 0);
    my $unmap = '';
    if (defined $ref->{Symmetrix}{Device}{Front_End}{Port}) {
        $unmap = '-unmap'
    }
    return $unmap;
}

