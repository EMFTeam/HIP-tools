package SFDate;

use Carp;

my @MONTH_TO_DAYS = (
	31, # Jan
	29, # Feb (no leap year garbage)
	31, # Mar
	30, # Apr
	31, # May
	30, # Jun
	31, # Jul
	31, # Aug
	30, # Sep
	31, # Oct
	30, # Nov
	31, # Dec
);

# cumulative days-of-year at start of any given month
my @MONTH_TO_DOY = ();

{
	my $doy = 0;
	
	for my $dom (@MONTH_TO_DAYS) {
		push @MONTHS_TO_DOY, $doy;
		$doy += $dom;
	}
}


# take a date string, parse it, validate it,
# and bless its representation compactly into
# an object. negative dates are not allowed,
# nor are dates beyond year 9999.
sub new {
	my $class = shift;
	my $date = shift;
	
	$date =~ /^(\d{1,4})\.(\d{1,2})\.(\d{1,2})$/o;
	my ($y, $m, $d) = (0+$1, 0+$2, 0+$3);

	croak "invalid date: $date"
		unless $y && $m && $d && $m <= 12 && $d <= $MONTH_TO_DAYS[$m-1];
	
	my $self = bless
		[
			$y,
			$m,
			$d,
		], $class;

	return $self;
}


# compare two dates in a manner suitable for use as a custom
# sort function.
sub cmp {
	return $a->[0] <=> $b->[0]
           ||
		   $a->[1] <=> $b->[1]
           ||
		   $a->[2] <=> $b->[2];
}


# given another SFDate, return the number of days between
# them; negative implies the left-hand side (first argument)
# SFDate is earlier, zero that they are the same date, and
# positive implies that right-hand-side is earlier
sub diff_days {
	return $_[0]->epoch_days() - $_[1]->epoch_days();
}

# can be used as a sort function too, though I think cmp
# should perform better.
sub cmp_days {
	return $a->epoch_days() <=> $b->epoch_days();
}


# CKII-style string format (not suitable for lexicographic
# comparison, though, due to lack of zero-padding).
sub str {
	return $_[0]->[0].'.'.$_[0]->[1].'.'.$_[0]->[2];
}


# for our terms, the epoch is 1.1.1 (first day AD), and
# each year has 365 days, though the months' durations,
# of course, vary. the number of days in a year until
# the beginning of a given month is used rather than
# individually calculating each months' contribution.
# there are no Gregorian leap <anything>, basically.
sub epoch_days {
	my $d = ($_[0]->[0] - 1)*365;
	$d += $MONTH_TO_DOY[ $_[0]->[1] - 1 ];
	$d += $_[0]->[2] - 1;
	return $d;
}


# given a number of days offset from our date (may be positive or negative),
# return a new SFDate representating the offset date.  useful for, say,
# calculating the date at which a [province/character/opinion] modifier will
# expire.
sub days_offset_date {
	croak; # TODO
}


1;

