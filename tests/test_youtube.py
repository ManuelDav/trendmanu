from trendmanu.youtube import YouTubeClient


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class FakeSearchRequest:
    def __init__(self):
        self.kwargs = None

    def list(self, **kwargs):
        self.kwargs = kwargs
        return FakeRequest(
            {
                "pageInfo": {"totalResults": 1234},
                "items": [
                    {"id": {"videoId": "a"}},
                    {"id": {"videoId": "b"}},
                ],
            }
        )


class FakeVideosRequest:
    def list(self, **kwargs):
        if kwargs.get("chart") == "mostPopular":
            return FakeRequest(
                {
                    "items": [
                        {
                            "snippet": {
                                "title": "Claudia Sheinbaum hoy",
                                "description": "#Sheinbaum #politica",
                                "tags": ["sheinbaum", "politica", "shorts", "youtube"],
                            }
                        },
                        {
                            "snippet": {
                                "title": "Partido de fútbol",
                                "description": "#futbol",
                                "tags": ["futbol", "deporte", "sheinbaum"],
                            }
                        },
                    ]
                }
            )
        return FakeRequest(
            {
                "items": [
                    {
                        "id": "a",
                        "snippet": {"title": "Video A"},
                        "statistics": {"viewCount": "1000"},
                    },
                    {
                        "id": "b",
                        "snippet": {"title": "Video B"},
                        "statistics": {"viewCount": "500"},
                    },
                ]
            }
        )


class FakeService:
    def __init__(self):
        self._search = FakeSearchRequest()
        self._videos = FakeVideosRequest()

    def search(self):
        return self._search

    def videos(self):
        return self._videos


def test_search_topic_sums_views_and_competition():
    client = YouTubeClient("fake-key", "MX", service=FakeService())
    metrics = client.search_topic("inteligencia artificial")
    assert metrics.available
    assert metrics.total_results == 1234
    assert metrics.videos_found == 2
    assert metrics.views_7d == 1500
    assert metrics.avg_views == 750
    assert metrics.top_video_title == "Video A"
    assert metrics.top_video_url == "https://www.youtube.com/watch?v=a"


def test_fetch_trending_topics_extracts_tags_and_hashtags():
    client = YouTubeClient("fake-key", "MX", service=FakeService())
    topics = client.fetch_trending_topics()
    names = {topic.topic for topic in topics}
    assert "sheinbaum" in names
    assert "futbol" in names
    assert "shorts" not in names
    assert "youtube" not in names
