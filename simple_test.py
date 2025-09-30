import requests

url = 'https://www.reddit.com/r/science/comments/1nu94z4/comment/nh05i30/.json?context=10000'
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers, timeout=3)
data = response.json()

post_data = data[0]['data']['children'][0]['data']
comments_data = data[1]['data']['children']

conversation = []

def extract_chain(comment_list, depth=0):
    print(f"Depth {depth}: Processing {len(comment_list)} items")

    if depth > 50:
        print("Hit depth limit!")
        return

    for i, item in enumerate(comment_list):
        print(f"  Item {i}: kind={item.get('kind')}")

        if item['kind'] != 't1':
            continue

        comment = item['data']
        author = comment['author']
        body_preview = comment['body'][:50]

        print(f"  -> Comment by {author}: {body_preview}...")
        conversation.append(f"{author}: {comment['body']}")

        replies = comment.get('replies')
        print(f"  -> Replies type: {type(replies)}")

        if replies and isinstance(replies, dict) and 'data' in replies:
            children = replies['data'].get('children', [])
            print(f"  -> Has {len(children)} children")
            if children:
                extract_chain(children, depth + 1)

        break

print("Starting extraction...")
extract_chain(comments_data)
print(f"\nTotal comments: {len(conversation)}")
for i, c in enumerate(conversation):
    print(f"{i+1}. {c[:80]}...")
