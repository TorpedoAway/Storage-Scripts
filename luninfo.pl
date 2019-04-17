#!/usr/bin/perl

use strict;
use warnings;

=pod
 
=head1 DESCRIPTION
 
This script has one mandatory parameter, --sid. 

The script reads a list of SRDF R1 devices from the file, r1_dev_list
in the same directory as the script. Format of the file is one R1 dev
per line. The script iterates over the list and runs appropriate SYMCLI
commands and uses the xml_e output format and XML::Simple module for
parsing the data.

=head1 USAGE

$0 --sid <Sym SID#> --ldev "ldev ldev ldev..."
 
 --ldev is an optional parameter and if supplied, the script takes the R1 list from 
 the commandline.

 --json is an optional parameter and if supplied, the script output is JSON formatted.

=head1 Examples

  ./luninfo.pl   --sid 0495   --ldev "06f4 06f6"
  ./luninfo.pl   --sid 0495   --ldev "06f4 06f6" --json

=cut

use Data::Dumper;
use Getopt::Long;
use XML::Simple;
use JSON qw( );

# Require root user
if ( $> != 0 ) {
    print "\n\nThis script requires root permissions.\n"; 
    print "Use su or sudo to become root before running this script.\n";
    print "\nExiting...\n";
    exit(1);
}

my %optctl = ();
GetOptions (\%optctl, "sid=i", "ldev=s", "json");

if (! exists($optctl{'sid'}) ) {
    print "USAGE $0 --sid <Array SID> --ldev \"06f4 06f6\"\n";
    print "USAGE $0 --sid <Array SID> --ldev \"06f4 06f6\" --json\n";
    print "NOTE: Alternatively, the devices to report on may be saved to a file named r1_dev_list.\n\n";
    exit(1);
}


my $sid         = $optctl{'sid'};
my $r1_dev_file = "r1_dev_list";
my $r1_devs     = get_r1_list();

my $report      = make_report();

if ( exists($optctl{'json'}) ) {
    my $json_obj = new JSON;
    my $json_text = $json_obj->pretty->encode($report);
    print "$json_text\n\n";
    exit();
}

foreach my $lun (keys %{$report->{LUNS}}) {
    print "Device=$lun\n";
    print "  R1        :     $report->{LUNS}{$lun}{R1NAME}\n";
    print "  R1SG      :     $report->{LUNS}{$lun}{R1SG}\n";
    print "  R1SID     :     " . substr($report->{LUNS}{$lun}{R1SID},-4) . "\n";
    print "  R1CFG     :     $report->{LUNS}{$lun}{R1CFG}\n";
    print "  DEVGRP    :     $report->{LUNS}{$lun}{DEVGRP}\n";
    print "  LDNAME    :     $report->{LUNS}{$lun}{LDNAME}\n";
    print "  R2        :     $report->{LUNS}{$lun}{R2}\n";
    print "  R2SG      :     $report->{LUNS}{$lun}{R2SG}\n";
    if ($report->{LUNS}{$lun}{R2SID} !~ /Not_Defined/) {
        print "  R2SID     :     " . substr($report->{LUNS}{$lun}{R2SID},-4) .  "\n";
    } else {
        print "  R2SID     :     SRDF is not configured for this LUN.\n";
    }
    print "  RDFGRP    :     $report->{LUNS}{$lun}{RDFGRP}\n";
    print "  RDFLABEL  :     $report->{LUNS}{$lun}{RDFLABEL}\n";
    print "  PAIRSTATE :     $report->{LUNS}{$lun}{PAIRSTATE}\n";
    print "  KB        :     $report->{LUNS}{$lun}{KB}\n";
    print "  CLONE     :     $report->{LUNS}{$lun}{CLONE}\n";
    print "  CYL       :     $report->{LUNS}{$lun}{CYL}\n\n";


}


sub make_report {
    my $report = {};
    my $groups = {};
    my $r1_sid;
    my $cmd = "symcfg -sid $sid list -rdfg all -output xml_e";
    my $xml = get_xml($cmd);
    my $ref = XMLin($xml, ForceArray => 0);
    foreach my $group ( @{$ref->{Symmetrix}{RdfGroup}} ) {
        $groups->{$group->{ra_group_num}} = $group->{ra_group_label};
    }

    foreach  my $r1_dev ( @{$r1_devs} ) {
        $cmd = "symdev -sid $sid show $r1_dev -output xml_e";
        $xml = get_xml($cmd);
        $ref = XMLin($xml, ForceArray => 0);
 
        my $cloned; 
        #print Dumper($ref);
        my $type = $ref->{Symmetrix}{Device}{CLONE_Device};
        #print "Clone_Device is an " . $type . "\n";
        if (defined $ref->{Symmetrix}{Device}{CLONE_Device}) {
            if ( $type =~ /array/i) {
                $cloned = "CLONES (SID-$sid): ";
                foreach my $pair (@{$ref->{Symmetrix}{Device}{CLONE_Device}}) {
                    my $clone_src = $pair->{SRC}{dev_name};
                    my $clone_tgt = $pair->{TGT}{dev_name};
                    my $dg_grp    = $pair->{TGT}{dg_group};
                    $cloned .= "$dg_grp: $clone_src --> $clone_tgt, ";
                }
            } else {
                my $clone_src = $ref->{Symmetrix}{Device}{CLONE_Device}{SRC}{dev_name};
                my $clone_tgt = $ref->{Symmetrix}{Device}{CLONE_Device}{TGT}{dev_name};
                my $dg_grp = $ref->{Symmetrix}{Device}{CLONE_Device}{TGT}{dg_group};
                $cloned = "CLONE (SID-$sid): $dg_grp: $clone_src --> $clone_tgt";
            }
        }
 
        if ( ( defined $ref->{Symmetrix}{Device}{RDF}{Local}{type} ) and
           ( $ref->{Symmetrix}{Device}{RDF}{Local}{type} =~ /R2/ ) ) {
            $r1_dev = $ref->{Symmetrix}{Device}{RDF}{Remote}{dev_name};
            $r1_sid = $ref->{Symmetrix}{Device}{RDF}{Remote}{remote_symid};
            $cmd = "symdev -sid $r1_sid show $r1_dev -output xml_e";
            $xml = get_xml($cmd);
            $ref = XMLin($xml, ForceArray => 0);            
        } 
        else {
            $r1_sid = $sid;
        }


        
        $report->{LUNS}{$r1_dev}{CLONE}     = $cloned;
        $report->{LUNS}{$r1_dev}{R1SID}     = $r1_sid;
        $report->{LUNS}{$r1_dev}{KB}        = $ref->{Symmetrix}{Device}{Capacity}{kilobytes};
        $report->{LUNS}{$r1_dev}{CYL}       = $ref->{Symmetrix}{Device}{Capacity}{cylinders};
        $report->{LUNS}{$r1_dev}{R2}        = $ref->{Symmetrix}{Device}{RDF}{Remote}{dev_name}; 
        $report->{LUNS}{$r1_dev}{R2SID}     = $ref->{Symmetrix}{Device}{RDF}{Remote}{remote_symid};
        $report->{LUNS}{$r1_dev}{PAIRSTATE} = $ref->{Symmetrix}{Device}{RDF}{RDF_Info}{pair_state};
        $report->{LUNS}{$r1_dev}{R1CFG}     = $ref->{Symmetrix}{Device}{Dev_Info}{configuration};
        $report->{LUNS}{$r1_dev}{R1NAME}    = $ref->{Symmetrix}{Device}{Dev_Info}{dev_name};
        $report->{LUNS}{$r1_dev}{DEVGRP}    = $ref->{Symmetrix}{Device}{Dev_Info}{device_group};
        $report->{LUNS}{$r1_dev}{LDNAME}    = $ref->{Symmetrix}{Device}{Dev_Info}{ld_name};
        $report->{LUNS}{$r1_dev}{RDFGRP}    = $ref->{Symmetrix}{Device}{RDF}{Local}{ra_group_num};
        $report->{LUNS}{$r1_dev}{RDFLABEL}  = 'Not_Defined';
        $report->{LUNS}{$r1_dev}{RDFLABEL}  = $groups->{$report->{LUNS}{$r1_dev}{RDFGRP}} 
                                     if (defined $report->{LUNS}{$r1_dev}{RDFGRP});
        


        # Set values for any undefined keys
        foreach my $key (keys %{$report->{LUNS}{$r1_dev}}) {
            $report->{LUNS}{$r1_dev}{$key} = 'Not_Defined' if (! defined $report->{LUNS}{$r1_dev}{$key});
        }
        my $r1sg = get_sg($report->{LUNS}{$r1_dev}{R1SID},$r1_dev);
        my $r2sg = 'Not_Defined';
        $r2sg = get_sg($report->{LUNS}{$r1_dev}{R2SID},$report->{LUNS}{$r1_dev}{R2})
                 if ($report->{LUNS}{$r1_dev}{R2} !~ /Not_Defined/);
        $report->{LUNS}{$r1_dev}{R1SG} = $r1sg;
        $report->{LUNS}{$r1_dev}{R2SG} = $r2sg;
    }

    return $report;
}

sub get_sg {
    my ($sid, $dev) = @_;
    my $command = "symaccess -sid $sid list -type storage -dev $dev -output xml_e";
    my $xml = get_xml($command);
    my $ref = XMLin($xml, ForceArray => 0);
    my $type = $ref->{Symmetrix}{Storage_Group};
    my $groups = "";
    if (defined $type) {
        if ( $type =~ /array/i) {
            foreach my $sg (@{$ref->{Symmetrix}{Storage_Group}}) {
                $groups .= "$sg->{Group_Info}{group_name} "
            }
        } else {
            $groups = $ref->{Symmetrix}{Storage_Group}{Group_Info}{group_name};
        }
    } else {
        $groups = "No_Storage_Group"
    }
    return $groups;
}


sub get_r1_list {
    my @r1_devs;
    if (! exists($optctl{'ldev'}) ) {
        open(my $fh, "<", $r1_dev_file)
            or die "Can't open $r1_dev_file : $! \n";
        while ( my $line = <$fh> ) {
            chomp($line);
            push @r1_devs, $line;
        }
    } 
    else {
        my $device = _trim($optctl{'ldev'});
        @r1_devs = split(/\s+/,$device);
    }
    #print Dumper(@r1_devs);
    return \@r1_devs;
}

sub get_xml {
    my $cmd = shift;
    my $xml = '';
    open(SYMDEV,"$cmd|") or die "Failed opening $cmd ($!)\n";
    while (my $line = <SYMDEV>) {
        $xml .= $line;
    }
    return $xml;
}


sub _trim {
    my $string = shift;
    chomp($string);
    $string =~ s/^\s+//g;
    $string =~ s/\s+$//g;
    return $string;
}


