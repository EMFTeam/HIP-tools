package SFWar;

use strict;
#use SFDate;
use SFWarCB;
use Class::Struct;

struct 'SFWar' => [
	name => '$',
	attackers => '@',
	defenders => '@',
	casus_belli => 'SFWarCB',
#	start_date => 'SFDate',
	warscore => '$',
];

sub primary_attacker {
	return $_[0]->[1]->[0];
}

sub primary_defender {
	return $_[0]->[2]->[0];
}


1;
