A Few Kallithea hooks and extensions
------------------------------------------------------------
No plugins can currently be configured from the Kallithea settings, so search for 'CHANGEME' in the files to customize for your setup.

**hooks/canpush.(py|sh)**
_____________________
Restricts push permissions more than kallithea does by default, by requiring explicit write permissions for your account, optionally even if you are the repo owner.  Intended to lock down 'production' streams from unintentional pushes.

**hooks/headcount.sh**
__________________
Standard mercurial hook that prevents anyone from pushing multiple heads to a repo.

**rcextensions/\_\_init\_\_.py**
________________________
The most interesting plugin, integration with the [jenkins continuous integration server](https://jenkins-ci.org/).

This will:

1. Create a new jenkins job when a repo is created using a default config.xml.
2. Copy the existing jenkins job when a repo is forked, updating the names and paths and optionally the permissions.
3. Delete a jenkins job when a repo is deleted.
4. Schedules builds on pushes.
5. It also creates or copies as stated in 1 & 2 when you push or pull to the repo, for example if you manually delete the jenkins job it will be re-created.
6. On push it tells you about the last job status, this is example text:

```
remote: Jenkins: No successful builds yet for someproject
remote: Jenkins: Last build failed:  http://somehost/jenkins/job/someproject/1/
remote: Jenkins: Scheduled polling of someproject successfully!
```

Issues:

1. Kallithea doesn't send the same information into all hooks, so I have to use the Kallithea API to fill in the blanks sometimes.  This needs fixed in Kallithea.
2. Kallithea doesn't have a hook for renaming or moving a repo, so the jenkins jobs end up getting orphaned.  This needs fixed in Kallithea.

Todo:

1. I'd like to use extra_fields as configuration for perhaps all of these plugins, but they currently aren't passed to plugins, and don't move with forks, making them useless.  Ideally there would be extra_fields on a global, group, and repo level, and they would move with forks.  These all need done in Kallithea first, then it's trivial to support them in the plugins.

LICENSE
-------
Everything here is licensed GPLv3 just like Kallithea itself.  Full license text can be found in gpl-3.0.txt.