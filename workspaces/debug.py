""" debug fuctionality """
import json

def workspacedebug(event, context, data):
    """ dumps, well, pretty much everything """
    #context_keys = [key for key in dir(context) if not key.startswith("_")]
    context_data = {
        'function_name' : context.function_name
    }
    #   "aws_request_id",
    #   "client_context",
    #   "function_name",
    #   "function_version",
    #   "get_remaining_time_in_millis",
    #   "identity",
    #   "invoked_function_arn",
    #   "log",
    #   "log_group_name",
    #   "log_stream_name",
    #   "memory_limit_in_mb"

    text = f"""EVENT DATA
```
{json.dumps(event, indent=2)}
```

CONTEXT DATA

```
{json.dumps(context_data, indent=2)}
```

DECODED BODY DATA
```
{json.dumps(data, indent=2)}
```"""
    return text
