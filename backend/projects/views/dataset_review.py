from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from labels.models import DatasetReview
from labels.serializers import DatasetReviewSerializer

class DatasetReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        serializer = DatasetReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DatasetReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        queryset = DatasetReview.objects.filter(example__project_id=project_id)
        serializer = DatasetReviewSerializer(queryset, many=True)
        return Response(serializer.data) 