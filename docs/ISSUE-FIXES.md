# Retired coding workspace and open issue fixes

The home-page OPPE card still opens https://oppe.rangalabs.cloud/ in a new tab.
The in-app editor, execution gateway, authoring API, bundled coding questions,
conversion tooling and their tests have been removed. Historical catalog exam
labels remain source metadata; they do not enable a coding workspace.

The last two migration IDs remain as inert compatibility markers. Existing
databases stamped with either revision can still upgrade; fresh installs do not
create or seed the retired tables. Existing database rows are not deleted.

## Result sharing (#3)

The generated PNG preview uses a browser blob URL. CSP now permits `blob:` for
images only. Scripts retain their existing restrictions. The WhatsApp action is
labelled “WhatsApp text”; attaching a PNG requires native image sharing or
downloading and attaching it manually.

## Calculator size (#4)

Drag the bottom-right corner to resize with a mouse, pen or touch. Focus that
control and use arrow keys for keyboard resizing. The calculator retains the
current expression, clamps size to the available viewport and scrolls its
contents when small.

## Google Drive source access (#1)

Catalog Sync now reports callback-origin errors, permission denial, expired
authorization and provider/configuration failures in the admin panel. The
authorization and token-exchange steps use the exact same stored callback URL.
Secure-cookie deployments use HTTPS even behind TLS termination. Account choice
is explicit. A prior account's refresh token is never reused for a new account.

Deployment setup is still necessary; repository code cannot supply private
Google credentials or change the Google Cloud project:

1. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET for a **Web
   application** client. Enable Google Drive API in that project.
2. Open Admin on the intended domain. In Catalog Sync, copy the displayed
   authorized redirect URI into the Google Cloud client's redirect URI list.
   `www` and the apex domain are different cookie hosts. If setting
   GOOGLE_OAUTH_REDIRECT_URI explicitly, use that exact same origin and callback
   path. Alternatively leave it empty to use the current admin origin.
3. If the Google consent app is in Testing, add the connecting Google/IITM
   account as a test user. Organization policy may require its administrator.
4. Connect, select the account that can open the source PDFs and grant Drive
   read access. If old credentials cannot be decrypted after SECRET_KEY changed,
   Disconnect, then connect again.

The connection flow is covered with mocked Google responses. Actual account
authorization and private-source downloads must be verified on the deployed
site before issue #1 can be considered verified end to end.
