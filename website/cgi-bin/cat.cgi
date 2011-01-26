#!/usr/bin/perl -T

use strict vars;
use CGI;
use HTML::Entities ();
use Digest::MD5 qw(md5 md5_hex);
use Crypt::RC4;
# require "/home/tonyh/public_html/etc/RC4.pm";

umask(02);
my $q = CGI->new;
my $debug = $q->param('debug') ? 1 : undef;
my $sharedsecret = 'zzxoiuakjwefya%^&@#*(*(&@dflaskiouioiuklasfq';

####### ########################### #######
####### # Print a file generated by xml2rfc.cgi and then remove it.
####### #
####### # invoking form has these fields:
####### #       file "input" - contains the file to output and remove
####### #
####### ########################### #######

printHeaders("text/plain") if $debug;
my $input   = $q->param('input');
userError("Invalid filename (empty)") if !defined($input);
userError("Invalid filename (bad format)") if ($input !~ /^([a-zA-Z0-9]*-[0-9]*)$/);
my $fn = decryptFileName($1);
userError("Invalid filename (wrong directory)", $fn) if (($fn !~ "^/tmp/") && ($fn !~ "^/var/tmp/"));
userError("Invalid filename (unwritable)") if (!-w $fn);
userError("Invalid filename (bad path)") if ($fn =~ "/../");

if ($fn =~ /\.xml$/) {
    my $outputfn = ($ENV{PATH_INFO} ne '') ? basename($ENV{PATH_INFO}) : basename($fn);
    printHeaders("application/octet-stream", "Content-Disposition: attachment; filename=\"$outputfn\"");
} else {
    printHeaders(getContentType($fn));
}
catFile($fn);
unlink($fn);

####### ########################### #######
####### # all done
####### ########################### #######


####### ########################### #######
####### #### utility functions
####### ########################### #######

####### use a given pattern to untaint a value
####### default to the entire value
sub untaint {
    my $str = shift;
    my $pat = shift;
    $pat = "(.*)" if !defined($pat);
    return $1 if ($str =~ /$pat/);
    return undef;
}

####### copy the contents of a file to standard output
sub catFile {
    my $fn = shift;
    if ( open(RAW, "<", $fn) ) {
	my $r;
	my $block;
	while (($r = read(RAW, $block, 4096)) > 0) {
	    print $block;
	}
	close(RAW);
    }
}

####### if not already generated, make sure there is a content 
####### type header, along with any other headers we will need
my $printedHeader;
sub printHeaders {
    my $contentType = shift;
    if (!$printedHeader || $debug) {
	print "Content-Type: $contentType\n";
	foreach my $hdr (@_) {
	    print "$hdr\n";
	}
	print "\n";
    }
    $printedHeader = 1;
}

####### for the given mode and format, return
####### a proper content-type value
sub getContentType {
    my $fn = shift;
    my $format = untaint($fn, "[.]([^.]*)\$");
    if ($format eq 'txt') { return "text/plain"; }
    if ($format eq 'html') { return "text/html"; }
    if ($format eq 'xml') { return "text/xml"; }
    if ($format eq 'pdf') { return "application/pdf"; }
    if ($format eq 'epub') { return "application/epub+zip"; }
    if ($format eq 'rtf') { return "application/rtf"; }
    if ($format eq 'ps') { return "application/postscript"; }
    if ($format eq 'nr') { return "application/nroff"; }
    return "application/octet-stream";
}

####### decrypt a filename so its path cannot be guessed
sub decryptFileName {
    my $in = shift;
    my ($rc4HexInput, $salt) = split(/-/, $in);
    my $rc4input = pack("H*", $rc4HexInput);
    my $passphrase = $sharedsecret . "-" . length($rc4input) . "-$salt";
    my $rc4 = Crypt::RC4->new( md5($passphrase) );
    return $rc4->RC4($rc4input);
}

####### print out an HTML page with a given error message
sub userError {
    printHeaders("text/html");
    print "<html><head><title>You lose</title></head><body>";
 
    my $event = HTML::Entities::encode(shift);
    my $info = HTML::Entities::encode(shift);

    print "<h1>$event</h1>\n";
    print "<pre>$info</pre>\n";
    print "<hr/>\n";
    print $ENV{SERVER_SIGNATURE};
    print "</body></html>\n";
    exit();
}

####### return the final path segment of a filename
sub basename {
    my $fn = shift;
    $fn =~ s/\\/\//g;
    $fn =~ s/^.*\///;
    return $fn;
}
