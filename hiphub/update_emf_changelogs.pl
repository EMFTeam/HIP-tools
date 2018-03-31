#!/usr/bin/perl

use strict;
use warnings;
use Carp;


my $INPUT_FILE = "EMF/EMF_changelog.txt"; # when hiphub invokes us, we are in the EMF repo root
my $SERVER_ROOT = "/var/www/hip.zijistark.com";
my $WEB_ROOT = "$SERVER_ROOT/pub";

my %CL_FILES = (
    header => "$WEB_ROOT/EMF_changelog_header.html",
    footer => "$WEB_ROOT/EMF_changelog_footer.html",
    uri => "/EMF_changelog_test.html",
);

my %BETA_CL_FILES = (
    header => "$WEB_ROOT/EMF_beta_changelog_header.html",
    footer => "$WEB_ROOT/EMF_changelog_footer.html",
    uri => "/EMF_BETA_changelog.html",
);

$CL_FILES{out} = $WEB_ROOT.$CL_FILES{uri};
$BETA_CL_FILES{out} = $WEB_ROOT.$BETA_CL_FILES{uri};

my %DLC_NAMES = (
    'RoI'      => 'Rajas of India',
    'CM'       => 'Charlemagne',
    'WoL'      => 'Way of Life',
    'HL'       => 'Horse Lords',
    'Conclave' => 'Conclave',
    'RD'       => "The Reaper's Due",
    'MnM'      => "Monks and Mystics",
    'JD'       => 'Jade Dragon',
);

my @MAJOR_VERSIONS = (
    '', # no 0.X versions (which would be RoI anyway)
    'RoI',
    'CM',
    'WoL',
    'HL',
    'Conclave',
    'RD',
    'MnM',
    'JD',
);


#########################################


sub can_read_files {
    for my $f (@_) {
        open(my $fh, '<', $f) or croak "open (for read): $!: $f";
        $fh->close;
    }
}

sub can_write_files {
    for my $f (@_) {
        my $tmp = !(-e $f);
        open(my $fh, '>>', $f) or croak "open (for write): $!: $f";
        $fh->close;
        unlink($f) if $tmp;
    }
}

can_read_files($INPUT_FILE, $CL_FILES{header}, $CL_FILES{footer}, $BETA_CL_FILES{header}, $BETA_CL_FILES{footer});
can_write_files( map { ($_, $_.'.tmp') } ($CL_FILES{out}, $BETA_CL_FILES{out}) );


#########################################


my %released_versions = (); # map a version like '1.01' to an optional release date, has a key for every version

my $indent = 0;
my $n_line = 0;
my $beta_body = '';
my $release_body = '';
my $body = undef;

open(my $cl_in, '<', $INPUT_FILE);

while (<$cl_in>) {
    ++$n_line;
    s/^\s+$//;

    if (/^EMF ([\d\.]+) \[BETA\]/i) {
        my $v = $1;
        $body = \$beta_body;
        $$body .= '<br/><br/><span class=cl_version_header>EMF v'.$v."-BETA</span>\n";
    }
    elsif (/^EMF ([\d\.]+) \[(\d{4}-\d{2}-\d{2})\]/i) {
        my $v = $1;
        $released_versions{$v} = $2;
        $body = \$release_body;
	my ($major, $minor) = split('.', $v);
	$$body .= "<a name='v${major}.X'/>\n" if ($minor =~ /^0+$/);
        $$body .= "<a name='v$v'/><br/><br/><span class=cl_version_header>EMF v$v</span><br/><i>Release Date: <b>$released_versions{$v}</b></i>\n";
    }
    elsif (/^EMF ([\d\.]+)/i) {
        my $v = $1;
        $released_versions{$v} = undef;
        $body = \$release_body;
	my ($major, $minor) = split('.', $v);	
	$$body .= "<a name='v${major}.X'/>\n" if ($minor =~ /^0+$/);
        $$body .= "<a name='v$v'/><br/><br/><span class=cl_version_header>EMF v$v</span><br/><i>Release Date: <b>N/A</b></i>\n";
    }
    elsif (/^([\t\x20]*)/) {
        croak "Changelog content found before finding its associated version on line $n_line!" unless defined $body;
        my $ws = $1;
        $ws =~ s/\x20{4}/\t/g;
        croak "Indentation consists of spaces that are not consecutive runs of 4 on line $n_line!" if ($ws =~ /\x20/);

        my $n_tabs = length($ws);
        
        # Can only increase indent by 1 tab at a time
        croak "Too many tabs prefixing line $n_line! Can only indent once per changelog item." if $n_tabs > $indent+1;
        
        if ($n_tabs > $indent) {
            $$body .= "<ul>\n";
            ++$indent;
        }
        
        # Can decrease indent all the way to 0 in one line, however
        
        if ($n_tabs < $indent) {
            my $dedent = $indent - $n_tabs;
            
            for (1 .. $dedent) { $$body .= "</ul>"; }
            
            $$body .= "\n";
            $indent = $n_tabs;
        }
        
        s/(^\t+)//g;
        
        if (/\S+/) {
            $$body .= "<li/>" if $indent;
            
            s|&|&amp;|g;
            s|<|&lt;|g;
            s|>|&gt;|g;

            # Some basic MarkDown-like formatting & helpers

            # Latin ought be italicized
            s|([iI]\.e\.),|<i>$1</i>,|g;
            s|([eE]\.g\.),|<i>$1</i>,|g;
            s|([cC]\.f\.),|<i>$1</i>,|g;
            s|([cC]\.(a\.)?),|<i>$1</i>,|g;
            s|, (i\.e\.)|, <i>$1</i>|g;
            s|, (e\.g\.)|, <i>$1</i>|g;
            s|\b(ceteris paribus)\b|<i>$1</i>|g;
            s|\b(caveat emptor)\b|<i>$1</i>|g;
            s|\b(ad infinitum)\b|<i>$1</i>|g;
            s|\b(ad nauseam)\b|<i>$1</i>|g;
            s|\b(a priori)\b|<i>$1</i>|g;
            s|\b(a posteriori)\b|<i>$1</i>|g;
            s|\b(de facto)\b|<i>$1</i>|g;
            s|\b(de jure)\b|<i>$1</i>|g;
            s|\b(et al)\b|<i>$1</i>|g;

            s|\[(Only )?SWMH( Only)?\]|<b>\[ <font color="#00b3b3">SWMH ONLY</font> \]</b>|gi;
            s|\((Only )?SWMH( Only)?\)|<b>\[ <font color="#00b3b3">SWMH ONLY</font> \]</b>|gi;
            s|\[(EMF\+)?Vanilla\]|<b>\[ <font color="#00b3b3">VANILLA MAP ONLY</font> \]</b>|gi;
            s|\((EMF\+)?Vanilla\)|<b>\[ <font color="#00b3b3">VANILLA MAP ONLY</font> \]</b>|gi;
            s|\[Vanilla Map\]|<b>\[ <font color="#00b3b3">VANILLA MAP ONLY</font> \]</b>|gi;
            s|\(Vanilla Map\)|<b>\[ <font color="#00b3b3">VANILLA MAP ONLY</font> \]</b>|gi;

            # standard stuff
            s|\*\*\*([^*]+?)\*\*\*|<b><i>$1</b></i>|g;
            s|\*\*([^*]+?)\*\*|<b>$1</b>|g;
            s|\*\`([^`]+?)\`\*|<b><span class=cl_inline_code>$1</span></b>|g;
            s|\*([^*]+?)\*|<i>$1</i>|g;
            s|\`([^`]+?)\`|<span class=cl_inline_code>$1</span>|g;
            s|__([^_]+?)__|<u>$1</u>|g;
            s|~~?([^_]+?)~~?|<s>$1</s>|g;

            $$body .= $_;
        }
    }
    else {
        croak "Unrecognized changelog line at line $n_line of input!";
    }
}

croak "No release content found!" unless $release_body;

my @rel_versions = sort { $b->{major} <=> $a->{major} || $b->{minor} <=> $a->{minor} }
                   map { unpack_release_version($_, $released_versions{$_}) }
                   keys %released_versions;

my $latest_vstr = $rel_versions[0]->{vstr};
my $latest_date = $rel_versions[0]->{date};

unless ($beta_body) {
    $beta_body = <<EOS;
<b><i>At the moment, the latest version of the EMF Beta is equivalent to the <a href='$CL_FILES{uri}#$latest_vstr'>latest released
version</a>, <b>EMF $latest_vstr</b>, which was released on <b>$latest_date</b>. Come back when we've had a chance to get some more work done and vetted for public testing!</i></b>
EOS
}

my $toc = "<ul>\n";

for my $mv (sort { $b <=> $a } 1..$#MAJOR_VERSIONS) {
    my $dlc_short = $MAJOR_VERSIONS[$mv];
    my $dlc_long = $DLC_NAMES{$dlc_short};
    my $dlc_fancy = ($dlc_short eq $dlc_long) ? $dlc_short : "$dlc_short ($dlc_long)";
    my $mv_full = "v${mv}.X";
    $toc .= "<li/><a href='$CL_FILES{uri}#$mv_full'>EMF $mv_full &mdash; $dlc_fancy\n";
    $toc .= "<ul>\n";
    
    for my $v (grep { $_->{major} == $mv } @rel_versions) {
	my $release_date = (!$v->{date}) ? "" : "<span class=tocreleasedate>[$v->{date}]</span>";
	$toc .= "<li/><a href='$CL_FILES{uri}#$v->{vstr}'>EMF $v->{vstr}</a> $release_date";
    }
    
    $toc .= "</ul>\n";
}

$toc .= "</ul>\n<hr>";

my $cl_tmp = $CL_FILES{out}.".tmp";
my $cmd = "cat $CL_FILES{header} > $cl_tmp";
(system($cmd) == 0) or croak "$cmd: nonzero exit status of $?";
open(my $of, '>>', $cl_tmp);
$of->print($toc);
$of->print($release_body);
$of->close() or croak "close: $cl_tmp: $!";
$cmd = "cat $CL_FILES{footer} >> $cl_tmp";
(system($cmd) == 0) or croak "$cmd: nonzero exit status of $?";

my $bcl_tmp = $BETA_CL_FILES{out}.".tmp";
$cmd = "cat $BETA_CL_FILES{header} > $bcl_tmp";
(system($cmd) == 0) or croak "$cmd: nonzero exit status of $?";
open($of, '>>', $bcl_tmp);
$of->print($beta_body);
$of->close() or croak "close: $bcl_tmp: $!";
$cmd = "cat $BETA_CL_FILES{footer} >> $bcl_tmp";
(system($cmd) == 0) or croak "$cmd: nonzero exit status of $?";

rename($cl_tmp, $CL_FILES{out}) or croak "rename: $cl_tmp --> $CL_FILES{out}: $!";
rename($bcl_tmp, $BETA_CL_FILES{out}) or croak "rename: $bcl_tmp --> $BETA_CL_FILES{out}: $!";

exit 0;


sub unpack_release_version {
    my ($vstr, $date) = @_;
    my ($major, $minor) = map { int } split(/\./, $vstr);
    return { major => $major, minor => $minor, vstr => $vstr, date => $date };
}
