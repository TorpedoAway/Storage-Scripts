#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;
use Getopt::Long;
use XML::Simple;
use JSON qw( );

my %optctl = ();
GetOptions (\%optctl, "sid=s");

if (! exists($optctl{'sid'}) ) {
    print "USAGE $0 --sid <SID>\n";
    exit(1);
}

my $sid = $optctl{'sid'};

my $cap = get_capacity($sid);

print "$sid $cap\n";

sub get_capacity {
    my ($sid) = shift;
    my $command = "symcfg -sid $sid list -thin -pool -gb -output xml_e";
    my $xml = get_xml($command);
    my $ref = XMLin($xml, ForceArray => 0);
    my $type = $ref->{Symmetrix}{Totals};
    my $percent_used = '';
    if (defined $type) {
            $percent_used = $ref->{Symmetrix}{Totals}{percent_full};
    } else {
            $percent_used = "Unknown"
    }

    return $percent_used;
}


sub get_sg {
    my ($sid, $dev) = @_;
    print "$sid, $dev\n";
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



sub get_dev {
    my ($sid, $dev) = @_;
    my $command = "symdev -sid $sid show $dev -output xml_e";
    my $xml = get_xml($command);
    my $ref = XMLin($xml, ForceArray => 0);
    return $ref;
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


