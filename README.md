# Odoo Sentry connector

an Odoo v10.0 module that connects your odoo deployment with [sentry](https://www.getsentry.com)

![Screen shot](screenshot.png?raw=true "Sample Screen")

## Installation

### On Odoo server
you need to install raven or make it available on odoo's python path.
`sudo pip install raven`

### Configure a sentry project

first you need to [install](http://sentry.readthedocs.org/en/latest/) Sentry or [buy](https://www.getsentry.com/pricing/) a hosted service from them.

login to your sentry account and create new project, go to project settings and copy `dsn` *data source name*.
open your Odoo config file and put a new config option `sentry_client_dsn` equal to dsn of your project.

now restart odoo server and install `odoo_sentry` module.

go to your sentry project and open `Stream` tab, you will see a message titled *Starting Odoo Server*. congratulation.

Other options are available to extends log level details ([odoo-sentry-sample.conf](odoo-sentry-sample.conf)):

- `sentry_enable_logging`: *default `false`*. set it to true will capture all logging that are logged through python standard logging module.
- `sentry_allow_orm_warning`: *default `false`*. enabling this will capture Odoo's warning exceptions (e.g. `except_osv`, `openerp.exceptions.Warning`).
- `sentry_include_context`: *default `false`*. this will add details about the odoo user that triggers specific event, plus database name, will displayed in Sentry additional info.
- `sentry_error_level`: *default `warning`*. select the minimum logging level that should be propagated to Sentry.
- `sentry_release`: *defaults to Odoo version`*. define your project's release here.

You can also set other Raven options by defining `sentry_options_<option here>`, eg. `sentry_options_environment = production` 
will tell Sentry the event came from the production environment.

Additionally, you can set some default context values and tags using `sentry_context_<context here>` or `sentry_context_tags_<tag key here>`. For example `sentry_context_tags_build = 20170516` would send the tag `build` with the value `20170516`.

### License
This project is licensed under [AGPL v3](http://www.gnu.org/licenses/agpl-3.0.html).

