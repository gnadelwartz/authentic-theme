#!/usr/bin/perl

#
# Authentic Theme (https://github.com/authentic-theme/authentic-theme)
# Copyright Ilia Rostovtsev <programming@rostovtsev.io>
# Licensed under MIT (https://github.com/authentic-theme/authentic-theme/blob/master/LICENSE)
#
use strict;

use File::Basename;

our (%in, %text, $cwd, $path);

require(dirname(__FILE__) . '/file-manager-lib.pm');

my @entries_list = get_entries_list();
my %errors;
my $status;
my $action     = $in{'action'};
my $delete     = $in{'delete'};
my $passphrase = decode_base64($in{'passphrase'});

my %webminconfig = foreign_config("webmin");
my $gpgpath = quotemeta($webminconfig{'gpg'} || "gpg");
my $no_command;

foreach my $name (@entries_list) {
    next if (-d "$cwd/$name");
    my $localtime = POSIX::strftime('%Y%m%d-%H%M%S', localtime());
    my ($iname, $fname, $fext);
    my $gpg;

    $iname = $name;
    $iname =~ s/\.(gpg|pgp)$// if ($action eq "decrypt");
    ($fname, $fext) = $iname =~ /^(?|(.*)\.(tar\.gz)|(.*)\.(.*)|(.*))$/;
    $iname  = $fname . "_" . $action . "ed_$localtime." . $fext;
    $status = 0;

    if ($action eq "encrypt") {
        my $key = quotemeta($in{'key'});
        $gpg =
"cd @{[quotemeta($cwd)]} && $gpgpath --encrypt --always-trust --output @{[quotemeta($iname)]}.gpg --recipient $key @{[quotemeta($name)]}";
        $status = system($gpg);

    } elsif ($action eq "decrypt") {
        my $extra;
        if ($passphrase) {
            $extra = (" --batch --yes --passphrase-fd 0 ");
        }
        $gpg = "cd @{[quotemeta($cwd)]} && $gpgpath $extra --output @{[quotemeta($iname)]} --decrypt @{[quotemeta($name)]}";
    }
    open my $fh => "| $gpg" or $no_command = 1;
    print $fh quotemeta($passphrase);
    close $fh;
    $status = $?;

    if ($delete && $status == 0) {
        unlink_file("$cwd/$name");
    }

    if (!has_command($gpgpath) || $no_command) {
        $errors{ $text{'theme_global_error'} } = text('theme_xhred_global_no_such_command', $gpgpath);
    }
    if ($status != 0) {
        if ($status == 512) {
            $errors{ html_escape($name) } = $text{'filemanager_archive_gpg_private_error'};
        }
    }
}

redirect('list.cgi?path=' . urlize($path) . '&module=' . $in{'module'} . '&error=' . get_errors(\%errors) . extra_query());
