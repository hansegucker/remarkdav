Changelog
=========

v1.0
----
* Update dependencies

v1.0-beta4
----------
* Use rmapi for uploading documents instead of rmapy because files uploaded by rmapy seems to be corrupt sometimes

v1.0-beta3
----------
* Rerun webdav operations in case of failure
* Check PDF files for validity
* Optimize download threads (keep a maximum of operations)
* Improve log prints

v1.0-beta2
----------
* Catch exceptions
* Ensure that files aren't downloaded twice
* Update dependencies

v1.0-beta
---------
* Switch to other version branch and downgrade required Python version to 3.7

v0.1.0-beta2
------------
* Upload a PDF to reMarkable cloud with meta information about the last successful sync (#7)
* Add configuration option for the path of the synchronisation DB (#3)
* Update some dependencies

v0.1.0-beta
-----------
* Add first working version which allows syncing PDF files from webdav to reMarkable cloud
