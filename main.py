import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import arxiv
import openai
import random

openai.api_key = os.environ["OPENAI_API_KEY"]
SLACK_CHANNEL = "#notifications"
KEYWORDS = ["time series",
            "self supervised",
            "world model",
            "LLM",
            "diffusion model",
            "generative model"]


def post_paper(keyword, client, num_papers=3):
    search = arxiv.Search(
        query=f'ti:%22 {keyword} %22',
        max_results=100,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    results = [r for r in search.results()]

    if len(results) < num_papers:
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text="=" * 50 + "\n" +
            f"{keyword}に関する最新の論文が{len(results)}本あります\n" + "=" * 50
        )
    else:
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text="=" * 50 + "\n" +
            f"{keyword}に関する最新の論文を{num_papers}本お届けします\n" + "=" * 50
        )
        results = random.sample([r for r in search.results()], k=num_papers)

    for i, result in enumerate(results):
        try:
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=str(i+1) + "本目\n" + get_summary(result)
            )
            print(f"Message posted: {response['ts']}")
        except SlackApiError as e:
            print(f"Error posting message: {e}")


def get_summary(result):
    system = """与えられた論文の要点を3点のみでまとめ、以下のフォーマットで日本語で出力してください。```
    タイトルの日本語訳
    ・要点1
    ・要点2
    ・要点3
    ```"""

    text = f"title: {result.title}\nbody: {result.summary}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': text}
        ],
        temperature=0.25,
    )
    summary = response['choices'][0]['message']['content']
    title_en = result.title
    title, *body = summary.split('\n')
    body = '\n'.join(body)
    date_str = result.published.strftime("%Y-%m-%d %H:%M:%S")
    message = f"発行日: {date_str}\n{result.entry_id}\n{title_en}\n{title}\n{body}\n"

    return message


def main(event, context):
    client = WebClient(token=os.environ["SLACK_API_TOKEN"])
    for k in KEYWORDS:
        post_paper(k, client)


if __name__ == "__main__":
    main(None, None)
