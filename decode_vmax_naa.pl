#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;
use Getopt::Long;

my %optctl = ();
GetOptions (\%optctl, "naa=s");


if (! defined $optctl{'naa'}) {
     print "USAGE $0 --naa <naa_number>\n";
     exit(1);
}
my $naa = $optctl{'naa'};

my $prefix = substr($naa, 0, 7);

if ($prefix eq "6000097") {
    my ($ser,$lun) = decode_vmax($naa);
    print "$naa is a VMAX TDEV. Array: $ser TDEV: $lun\n";
    exit(0);
}


sub decode_vmax {
    my $naa = shift;
    my $ldev = substr($naa, -8);
    my $sn   = substr($naa, -16);
    my $ser  = substr($sn, 0, 4);
    my $a = hex_decode(substr($ldev, 0, 2));
    my $b = hex_decode(substr($ldev, 2, 2));
    my $c = hex_decode(substr($ldev, 4, 2));
    my $d = hex_decode(substr($ldev, 6, 2));
    $ldev = $a . $b . $c . $d;
    return $ser, $ldev;
}

sub hex_decode {
    my $code = shift;
    my $key = substr($code,0,1);
    my $bit = substr($code, -1);
    if ($key == 3) {
        $bit = $bit;
    }  else {
        $bit += 9;
        $bit = sprintf("%X",     $bit);
    }
    return $bit;
}
