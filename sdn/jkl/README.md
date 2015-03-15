### Intranet Diagnostics Tool
This project is used to determine the paths taken by a packet flooded over an intranet.

By analyzing this information we can determine the best routes for differing packet types/sizes, as well as understand the flow of these packets
To use this application there are a couple necessary steps

1. You must run `./pox.py misc.full_payload SuperSimple3`
 - This is run from the **pox** server
 - This is found at the `/project/adv-net-samples/sdn/pox` directory
2. Once that command is running you must then initialize the application by running `./sender2.py`
 - This is run from the **sender** server
 - This is found at `/project/adv-net-samples/sdn/jkl` directoyr