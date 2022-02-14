# vrm-py

A very simple Python class for getting a basic summary of your VRM installations.

## Example

```
from vrm_client import VrmClient

vrm = VrmClient(username="username@domain.com", password="MyP@$$w0rd!")
print(vrm.summary())
```