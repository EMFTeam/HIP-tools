package SFWarCB;

use strict;
use SFDate;
use Class::Struct;

struct 'SFWarCB' => [
	name => '$',
	actor => '$',
	recipient => '$',
	thirdparty => '$',
	landed_title => '$',
	date => 'SFDate',
];


sub is_landed {
	return ($_[0]->[3]) ? 1 : 0;
}


1;
