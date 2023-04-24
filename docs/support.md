# Support

Please use the [issue tracker at GitHub](https://github.com/pepkit/looper/issues) to file bug reports or feature requests.

Looper supports Python 2.7 and Python 3, and has been tested in Linux. If you clone this repository and then an attempt at local installation, e.g. with `pip install --upgrade ./`, fails, this may be due to an issue with `setuptools` and `six`. A `FileNotFoundError` (Python 3) or an `IOError` (Python2), with a message/traceback about a nonexistent `METADATA` file means that this is even more likely the cause. To get around this, you can first manually `pip install --upgrade six` or `pip install six==1.11.0`, as upgrading from `six` from 1.10.0 to 1.11.0 resolves this issue, then retry the `looper` installation.
