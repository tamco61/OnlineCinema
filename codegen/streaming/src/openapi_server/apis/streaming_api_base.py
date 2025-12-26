# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictStr
from typing import Any
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.progress_update_request import ProgressUpdateRequest
from openapi_server.models.progress_update_response import ProgressUpdateResponse
from openapi_server.models.stream_request import StreamRequest
from openapi_server.models.stream_response import StreamResponse
from openapi_server.models.watch_progress_response import WatchProgressResponse


class BaseStreamingApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseStreamingApi.subclasses = BaseStreamingApi.subclasses + (cls,)
    async def start_streaming_api_v1_stream_movie_id_post(
        self,
        movie_id: StrictStr,
        authorization: StrictStr,
        stream_request: StreamRequest,
    ) -> StreamResponse:
        """Start streaming a movie  **Access Control:** - Requires valid JWT token - Requires active subscription  **Returns:** - Signed URL for HLS/DASH manifest - URL expires in 1 hour  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id} \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;manifest_type\&quot;: \&quot;hls\&quot;}&#39; &#x60;&#x60;&#x60;"""
        ...


    async def get_watch_progress_api_v1_stream_movie_id_progress_get(
        self,
        movie_id: StrictStr,
        authorization: StrictStr,
    ) -> WatchProgressResponse:
        """Get current watch progress  **Returns:** - Current playback position - Last watched timestamp  **Example:** &#x60;&#x60;&#x60;bash curl http://localhost:8005/api/v1/stream/{movie_id}/progress \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; &#x60;&#x60;&#x60;"""
        ...


    async def update_watch_progress_api_v1_stream_movie_id_progress_post(
        self,
        movie_id: StrictStr,
        authorization: StrictStr,
        progress_update_request: ProgressUpdateRequest,
    ) -> ProgressUpdateResponse:
        """Update watch progress  **Tracking:** - Saved to Redis (fast access) - Synced to PostgreSQL (persistent storage) - Kafka event published  **Client should call this endpoint periodically (e.g., every 10 seconds)**  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/progress \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;position_seconds\&quot;: 120}&#39; &#x60;&#x60;&#x60;"""
        ...


    async def stop_streaming_api_v1_stream_movie_id_stop_post(
        self,
        movie_id: StrictStr,
        authorization: StrictStr,
        progress_update_request: ProgressUpdateRequest,
    ) -> object:
        """Stop streaming session  **Actions:** - Updates final watch progress - Publishes stream.stop event - Ends stream session  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/stop \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;position_seconds\&quot;: 1800}&#39; &#x60;&#x60;&#x60;"""
        ...
