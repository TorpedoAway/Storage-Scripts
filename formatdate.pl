#!/usr/bin/perl

use POSIX;






my $date =  strftime "%m/%d/%Y:%H:%M" , localtime(time - (24*60*60));

print $date;
