import requests
import os


def load_llm_prompt(mode="standard"):
    """Load the LLM prompt from the text file and adjust for the selected mode.

    Args:
        mode: One of "friendly", "standard", "dunk", or "agree"
    """
    prompt_path = os.path.join(os.path.dirname(__file__), 'llm_prompt.txt')
    with open(prompt_path, 'r') as f:
        prompt = f.read()

    # Default replacements shared across modes
    stance_instruction = "Take a politically conservative stance on the issue being argued. You're here to disagree and present a counter-perspective."
    tone_instruction = "STANDARD MODE: Be direct, fact-based, and to the point - think Ben Shapiro style. Present your conservative perspective with clarity and confidence. You're not here to be friendly, but you're also not overtly aggressive. State facts, make logical arguments, and directly challenge flawed reasoning. Use a matter-of-fact tone that says 'here's why you're wrong' without being unnecessarily combative. Be assertive and unapologetic about your position, but let the facts do the heavy lifting rather than personal attacks."
    mode_specific_guidance = ""
    length_requirement = "LENGTH MATCHING IS MANDATORY: Your final comment MUST be approximately the same length as the comment you're responding to (the last comment in the chain). You may be 1-2 sentences longer, but NO MORE. This is about matching the effort level of the person you're responding to."
    phase2_requirements = (
        "Show your strategic thinking:\n"
        "- Analyze the opponent's last comment in detail\n"
        "- Identify their main claims, assumptions, and logical structure\n"
        "- Assess the strength of their argument and potential weaknesses\n"
        "- Consider how your research findings (if applicable) or logical reasoning can effectively counter their points\n"
        "- EXPLICITLY WRITE OUT your strategic analysis before moving to the next phase"
    )
    phase3_requirements = (
        "Show your counter-response predictions:\n"
        "- Identify ALL possible counter-responses the opponent might make to your reply\n"
        "- Assign probability weights (%) to EACH potential counter-response\n"
        "- List them out explicitly (e.g., \"Response A: 40%, Response B: 30%, Response C: 20%, Response D: 10%\")\n"
        "- Explain which high-probability responses you will preemptively address and HOW\n"
        "- SHOW ALL OF THIS ANALYSIS in your response before moving to the next phase"
    )
    phase4_length_target = "Set your target length: approximately the same length, or at most 1-2 sentences longer"
    phase4_counter_guidance = "- Explain how you'll preemptively address the most likely counter-responses in each draft"

    # Replace placeholders based on mode
    if mode == "friendly":
        stance_instruction = "Take the most objective, well-reasoned position on the topic, regardless of whether it strictly aligns with conservative ideology. Your goal is to find common ground and contribute meaningfully to the discussion."
        tone_instruction = "FRIENDLY MODE: Use a warm, thoughtful, and genuinely respectful tone. You're here to share insights and engage in meaningful dialogue. Be personable and open-minded - like you're having a conversation with a friend over coffee. Focus on understanding their perspective while offering your own thoughtful take. Use phrases like 'That's an interesting point,' 'I can see where you're coming from,' 'Here's how I think about it,' or 'What if we considered...' Avoid any hint of confrontation or debate."
    elif mode == "dunk":
        stance_instruction = "Take a politically conservative stance on the issue being argued. Your goal is to completely dismantle the opposing position."
        tone_instruction = "DUNK MODE ACTIVATED: Be ruthless, cutting, and mercilessly critical. Call out weak reasoning, expose logical fallacies by name, and demolish their argument piece by piece. Use sharp, incisive language that leaves no room for their position. Be unapologetically aggressive while staying factually grounded. The goal is to completely dismantle their argument and make them regret engaging. This is a debate, and you're here to win decisively."
    elif mode == "agree":
        stance_instruction = (
            "AGREE MODE: You are aligned with the final commenter. Reinforce their core points, add supporting context, and strengthen their position without undermining it."
        )
        tone_instruction = (
            "AGREE MODE TONE: Be encouraging, confident, and collaborative. Sound like a thoughtful ally who appreciates the original point and is eager to build on it with useful detail or personal insight."
        )
        mode_specific_guidance = (
            "AGREE MODE DIRECTIVE: This is not a debate. Focus on amplifying and enhancing the final comment rather than arguing against anyone."
        )
        length_requirement = (
            "LENGTH FLEXIBILITY: Aim to match the length of the comment you're supporting, but you may go up to roughly 150% of its length if needed to add meaningful reinforcement or context."
        )
        phase2_requirements = (
            "Agree mode is collaborative, so no strategic takedown is needed. Provide a brief note such as \"Strategic Analysis: N/A - Agree mode (reinforcing, not debating).\""
        )
        phase3_requirements = (
            "Agree mode does not require anticipating counter-responses. Provide a note such as \"Counter-Response Prediction: N/A - Agree mode.\""
        )
        phase4_length_target = (
            "Set your target length to roughly match the original comment, with permission to go up to about 150% if that's helpful for reinforcement"
        )
        phase4_counter_guidance = (
            "- Instead of counter-response planning, explain how each draft will reinforce and expand on the original comment while keeping the supportive tone consistent"
        )

    prompt = prompt.replace('{{STANCE}}', stance_instruction)
    prompt = prompt.replace('{{TONE}}', tone_instruction)
    prompt = prompt.replace('{{MODE_SPECIFIC_GUIDANCE}}', mode_specific_guidance)
    prompt = prompt.replace('{{LENGTH_REQUIREMENT}}', length_requirement)
    prompt = prompt.replace('{{PHASE2_REQUIREMENTS}}', phase2_requirements)
    prompt = prompt.replace('{{PHASE3_REQUIREMENTS}}', phase3_requirements)
    prompt = prompt.replace('{{PHASE4_LENGTH_TARGET}}', phase4_length_target)
    prompt = prompt.replace('{{PHASE4_COUNTER_GUIDANCE}}', phase4_counter_guidance)
    return prompt


def get_comment_chain(url, mode="standard"):
    """Scrape the comment chain from Reddit and return formatted text.

    Args:
        url: Reddit comment URL
        mode: One of "friendly", "standard", "dunk", or "agree"
    """

    # Extract comment ID from URL
    # URL format: .../comment/COMMENT_ID/...
    target_comment_id = None
    if '/comment/' in url:
        parts = url.split('/comment/')
        if len(parts) > 1:
            target_comment_id = parts[1].split('/')[0].split('?')[0]

    # Add ?context=10000 to get full parent chain
    base_url = url.split('?')[0]
    json_url = base_url + '.json?context=10000'

    # Set a user agent to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(json_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # Extract the comment thread
    # data[0] is the post, data[1] is the comments
    post_data = data[0]['data']['children'][0]['data']
    comments_data = data[1]['data']['children']

    # Build the conversation chain
    conversation = []

    # Add LLM instructions at the top
    instructions = load_llm_prompt(mode=mode)
    conversation.append(instructions)

    # Add the original post first
    post_author = post_data['author']
    post_title = post_data['title']
    post_body = post_data.get('selftext', '')
    post_url = post_data.get('url', '')

    # Build post content
    post_content = f"REDDIT POST:\n{post_author}: {post_title}"

    if post_body:
        post_content += f"\n\n{post_body}"

    # Add link if it exists and it's an external link (not reddit comments page)
    if post_url and '/comments/' not in post_url:
        post_content += f"\n\nLink: {post_url}"

    conversation.append(post_content)

    # Add comment section header
    conversation.append("COMMENT SECTION:")

    # Flag to stop extraction once we hit the target comment
    found_target = [False]

    def extract_chain(comment_list, depth=0):
        """Extract parent chain up to and including the linked comment."""
        if depth > 50 or found_target[0]:  # Stop if we found target or hit depth limit
            return

        for item in comment_list:
            if item['kind'] != 't1':  # Skip if not a comment
                continue

            comment = item['data']
            comment_id = comment['id']
            author = comment['author']
            body = comment['body']

            # Add this comment
            conversation.append(f"{author}: {body}")

            # Check if this is the target comment
            if target_comment_id and comment_id == target_comment_id:
                found_target[0] = True
                return

            # Follow replies to continue the chain
            replies = comment.get('replies')
            if replies and isinstance(replies, dict) and 'data' in replies:
                children = replies['data'].get('children', [])
                if children:
                    extract_chain(children, depth + 1)

            # Only process the first comment in each level (the direct chain)
            break

    extract_chain(comments_data)

    return conversation
