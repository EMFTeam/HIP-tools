package StringID;

use strict;
use warnings;
use Carp;

# container that proxies common string references, creating new unique
# integer identifiers for them when they've never been seen before and
# otherwise just returning the assigned unique integer ID for the
# string.  greatly improves the memory efficiency of references to and
# indexes upon things like 'catholic' or 'norse_pagan', especially if
# a lot of computing is done upon them (no point in using the literal
# values when you can use efficient integers).  reason I don't just use
# a direct hash value is because the result would be noncontiguous and
# also irreversible.  one needs to be able to convert these 'compressed'
# StringID values back to string form at some point, and one may want to
# make an array indexed by the unique integer IDs efficiently.

sub new {
	my $class = shift;
	
	my $self = bless
	{
	    str2id => {},
	    id2str => [],
	    top_id => -1,
	}, $class;
	
	for my $str (@_) {
	    $self->id($str);
	}

	return $self;
}


sub id {
    my ($self, $str) = @_;

    my $str2id = $self->{str2id};
    if (exists $str2id->{$str}) {
		return $str2id->{$str};
    }
    else {
		push @{ $self->{id2str} }, $str;
		++$self->{top_id};
		return $str2id->{$str} = $self->{top_id};
    }
}


sub str {
    my ($self, $id) = @_;
    return $self->{id2str}->[$id];
}



1;
