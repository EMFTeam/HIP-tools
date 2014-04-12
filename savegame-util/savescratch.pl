#!/usr/bin/perl

use strict;
use warnings;
use Carp;
use Time::HiRes qw(time);
use SaveFile;
use SFWar;
use SFWarCB;
use Class::Struct;
use List::Util qw(max);

croak "specify a filename" unless @ARGV;

my @sf = ();

for my $fn (@ARGV) {
	croak "invalid filename: $fn" unless -f $fn;
	push @sf, SaveFile->new($fn);
}

struct 'CBStats' => [
	name => '$',
	cb_save_pairs => '@',
	num_total => '$',
	in_saves => '%',
];

my %cb_stats = ();

for my $sf (@sf) {
	my $parse_start = time();
	$sf->parse();
	my $parse_end = time();

	print STDERR "Filename:        ", $sf->{filename}, "\n";
	print STDERR "Character count: ", (scalar keys %{ $sf->chars }), "\n";
	print STDERR "Active wars:     ", (scalar keys %{ $sf->wars }), "\n";
	print STDERR "Load time:       ", sprintf("%0.1f", $parse_end-$parse_start), "sec\n";

	for my $w (values %{$sf->wars}) {
		my $cb = $w->casus_belli;
		
		unless (exists $cb_stats{$cb->name}) {
			$cb_stats{$cb->name} = CBStats->new( name => $cb->name, cb => [[$cb, $sf]], num_total => 1, in_saves => { $sf->{filename} => 1 } );
		}
		else {
			my $cbs = $cb_stats{$cb->name};
			push( @{ $cbs->cb_save_pairs }, [$cb, $sf] );
			$cbs->num_total($cbs->num_total + 1);
			$cbs->in_saves($sf->{filename}, 1);
		}
	}
}

my @sorted_common_cbs = sort { (scalar keys %{$b->in_saves}) <=> (scalar keys %{$a->in_saves}) || $b->num_total <=> $a->num_total } values %cb_stats;

my $max_cbn_len = max map { length($_->name) } @sorted_common_cbs;

print sprintf("\n%-*s  %-5s  %-10s\n", $max_cbn_len, "\UCasus Belli", "\USaves", "\UActive Wars");

for my $cbs (@sorted_common_cbs) {
	print sprintf("%-*s %-5s  %-6d\n", $max_cbn_len, $cbs->name.':', (scalar keys %{$cbs->in_saves}).'/'.(scalar @sf), $cbs->num_total);
}


exit 0;
