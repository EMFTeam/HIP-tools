package SFReader;

sub new {
	my $class = shift;
	my $f = shift;
	
	my $self = bless
		[
			$f,
			0,
		], $class;

	return $self;
}

sub handle {
	return $_[0]->[0];
}

sub line {
	return $_[0]->[1];
}

sub next {
	my $l = $_[0]->[0]->getline();
	return undef unless defined $l;

	chomp $l;
	++$_[0]->[1];
	return $l;
}

sub getline {
	my $l = $_[0]->[0]->getline();
	return undef unless defined $l;
	
	++$_[0]->[1];
	return $l;
}

sub search_for_line {
	$_[1] .= $/ if ($_[2]);
	
	while (defined(my $l = $_[0]->getline())) {
		return 1 if $l eq $_[1];
	}
	
	return 0;
}

1;
