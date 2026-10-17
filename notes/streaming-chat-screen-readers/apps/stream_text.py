import time
# Deterministic streamed assistant reply (Markdown: two paragraphs, a three-item list, a closing sentence).
# Word-level tokens; ZETAEND marks the final word so an oracle can tell whether the end of the reply was spoken.
RESPONSE = ("Lyon sits where the Rhone meets the Saone, about four hundred kilometres southeast of Paris.\n\n"
            "Its old town is a protected heritage site, known for narrow covered passages called traboules.\n\n"
            "- Take the funicular up Fourviere hill.\n- Eat at a traditional bouchon.\n- Walk the Croix-Rousse slopes.\n\n"
            "Most visitors find two days enough to see the centre ZETAEND")
TOKENS = []
for i, w in enumerate(RESPONSE.split(" ")):
    TOKENS.append(w if i == 0 else " " + w)
FIRST_DELAY = 1.0
TOKEN_DELAY = 0.06
def tokens():
    time.sleep(FIRST_DELAY)
    for t in TOKENS:
        yield t
        time.sleep(TOKEN_DELAY)
if __name__ == "__main__":
    print(RESPONSE); print(len(TOKENS), "tokens")
