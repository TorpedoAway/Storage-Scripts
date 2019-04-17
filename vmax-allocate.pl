#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Long;
use POSIX;
use Data::Dumper;
use JSON qw( );


=pod

=head1 DESCRIPTION

This script has several mandatory parameters, (--sid, --chg, --cpm, --gb or --cyl, --count, --sg, --sid)

This is the Storage Ops VMAX LUN allocation script. It performs allocation and audits the
allocation for tracking purposes. 

=head1 USAGE

./vmax-allocate.pl  --sid <Sym SID#> --chg <CHGxxxx> --cpm <CPM#> --gb <Size in GB> --count <#luns to create> --sg <SG NAme>


 --chg       Service Now Change number
 --cpm       Capacity Approval info. This should be in the CHG description.
 --gb        Integer size in GB of desired allocation
 --cyl       Integer size in cylinders of desired allocation
 --count     Integer number of LUNs to be created of the size specified by --gb.
 --sg        Name of the SG to receive the LUN(s)
 --sid       SID of array used for allocation.
 --dryrun    Optional parameter. Just print out the symconfigure command.

=head1 Examples

  ./vmax-allocate.pl   --sid 1234 --chg CHG123456 --cpm "CMP Approval Info" --gb 100 --count 1 --sg tf_test_S
  ./vmax-allocate.pl   --sid 1234 --chg CHG123457 --cpm "CMP Approval Info" --cyl 1000 --count 3 --sg tf_test_S

=head1 Logs

  Allocations are recorded and sent to the Storage Ops Reporting Server. 
  Commands are logged to the following logfile on the CLI host where 
  vmax-allocate is executed.

  /usr/local/StorageOps/logs/allocation.log
 
=head1 Notes

  If all the inputs are validated the script will run symconfigure to create the LUNs. 
  All output will be captured and logged. If the symconfigure failes, the scripts will 
  exit with an appropriate error. If the symconfigure succeedes, the script will capture the 
  LUN IDs and log them. It will also format a JSON file to be forwarded to the reporting server.

  Once received by the reporting server the JSON file will be processed and added to an allocations database.
=cut


my $LOG = '/usr/local/StorageOps/logs/allocation.log';
my %auditlog;


# Require root user
if ( $> != 0 ) {
    print "\n\nThis script requires root permissions.\n";
    print "Use su or sudo to become root before running this script.\n";
    print "\nExiting...\n";
    exit(1);
}

$ENV{'PATH'} = '/opt/emc/SYMCLI/bin:/usr/bin:/usr/sbin:/usr/local/bin';

my %sgmap;
my %optctl = ();
GetOptions (\%optctl, "sid=i", "chg=s", "cpm=s", "sg=s", "count=i", "gb=i", "cyl=i", "dryrun");

my @RequiredOptions = qw(
    chg
    cpm
    count
    sg
    sid
);

# Verify we have required options
for my $opt (@RequiredOptions) {
    if (! exists($optctl{$opt}) ) {
        usage();
    }
}


my $total_cyls = 0;
my $gb = 0;
my $cyls = 1092.4;

# Also we need either cyl or gb specified
if (! exists($optctl{'gb'}) ) {
    if (! exists($optctl{'cyl'}) ) {
        usage();
    } else {
        $total_cyls = $optctl{'cyl'};
        $gb = ceil( (  $optctl{'cyl'} / $cyls ) * 2 );
    }
} else {
    $total_cyls = ceil( ( $cyls * $optctl{'gb'} ) / 2 );
    $gb = $optctl{'gb'};
}    

my $sg = $optctl{'sg'};    
my $sid = $optctl{'sid'};    
get_groups($sid);
if ( ! exists($sgmap{$sg})) {
    print "ERROR: SG $optctl{'sg'} does not exist. Exiting...\n";
    exit(1);
}

print "\n\nCommand Valid! Processing\n\n";

my $command = "symconfigure -sid " . $sid . " -cmd \"create dev count=" 
              . $optctl{'count'} . ", config=tdev, emulation=fba, size=" 
              . $total_cyls . " cyl, sg=" 
              . $sg . ";\" commit -nop";

if ( exists($optctl{'dryrun'}) ) {
    print "\nDry run output...\n\n$command\n";
    print "\nGB = $gb\n";
} else {
    write_log($LOG,"Processing CHG - $optctl{'chg'}");
    write_log($LOG,"Running Command - $command");
    print "Running Command - $command\n";
    my $output = runcmd($command);
    my $lun_ids;
    for my $line (@{$output}) {
        if ($line =~ /New symdev/) {
           my @line = split(/\s+/,$line);
           $lun_ids .= $line[2] . " ";
        }
    }
    write_log($LOG,"Created $lun_ids");
    $auditlog{'chg'} = $optctl{'chg'};
    $auditlog{'totalsize'} = $optctl{'count'} * $gb;
    $auditlog{'cpm'} = $optctl{'cpm'}; 
    $auditlog{'sid'} = $optctl{'sid'}; 
    $auditlog{'sg'} = $optctl{'sg'}; 
    $auditlog{'lun_ids'} = $lun_ids;
    $auditlog{'date'} = strftime "%m/%d/%Y", localtime;
    
    my $json_obj = new JSON;
    my $json_text = $json_obj->pretty->encode(\%auditlog);
    my $outputfile = '/usr/local/StorageOps/data/allocations/' . $optctl{'chg'} . '_' . time . '.json';
    open(my $fh, ">", $outputfile);
    print $fh $json_text;
    print $json_text;
}



sub usage {
    exec("/usr/bin/perldoc $0")
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
    my $outputfile = '/tmp/vmax-allocate.tmp.' . time;
    system("$command >$outputfile 2>&1") == 0
        or die "$0: symconfigure exited with return code " . ($? >>8) . "\n\nSee $outputfile for details.\n";

    open(my $fh, "<", $outputfile);
    while (my $line = <$fh>) {
        chomp($line);
        $line =~ s/^\s+//g;
        $line =~ s/\s+$//g;
        push @out, $line;
    }
    system("cat $outputfile >> $LOG");
    unlink($outputfile);
    return \@out
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

