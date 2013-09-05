These patches are necessary since testem saves temporary browsers' profiles
inside a fixed /tmp/testem.<browser> directory. This means that, when multiple
users are running tests in the same machine, the first one who runs the tests
creates those files and they're unreadable/unwritable for other users, hence
when they're running tests the entire suite hangs.
The current patches are just a momentary hack that creates random temp
directories for the profiles in order to solve this.

TODO(mario): remove these patches and upgrade testem when
https://github.com/airportyh/testem/issues/284 will be fixed.
