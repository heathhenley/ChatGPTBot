import tiktoken

# From: https://platform.openai.com/docs/guides/chat/introduction
def num_tokens(messages, model, prompt=""):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tks = 0
    for message in messages:
        num_tks += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tks += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tks += -1  # role is always required and always 1 token
    num_tks += 2  # every reply is primed with <im_start>assistant
    return num_tks + len(encoding.encode(prompt))
