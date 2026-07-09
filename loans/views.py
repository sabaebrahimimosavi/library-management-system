from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import permissions
from rest_framework import viewsets

from rest_framework.decorators import action
from rest_framework.response import Response

from books.models import Book

from accounts.permissions import IsMember

from .models import Loan

from .serializers import (
    LoanSerializer,
    BorrowBookSerializer,
)

from .services import LoanService

from .permissions import (
    IsLoanOwnerOrAdmin,
)


class LoanViewSet(
    viewsets.ModelViewSet
):
    queryset = Loan.objects.all()

    serializer_class = LoanSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowBookSerializer

        return LoanSerializer

    def get_queryset(self):

        if getattr(self, "swagger_fake_view", False):
            return Loan.objects.none()

        user = self.request.user

        if user.role == user.Roles.ADMIN:
            return Loan.objects.select_related(
                "user",
                "book",
            )

        return Loan.objects.select_related(
            "user",
            "book",
        ).filter(
            user=user
        )

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = get_object_or_404(
            Book,
            pk=serializer.validated_data["book"]
        )

        try:
            loan = LoanService.borrow_book(
                user=request.user,
                book=book
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LoanSerializer(loan).data,
            status=status.HTTP_201_CREATED,
        )

    
    @action(
        detail=True,
        methods=["post"],
    )
    def return_book(
        self,
        request,
        pk=None,
    ):
        loan = self.get_object()

        try:

            LoanService.return_book(
                loan=loan
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail":
                    "Book returned successfully."
            }
        )

    def get_permissions(self):

        # Borrowing and returning are member-only transactions — admins
        # manage the catalog/members and can view every loan, but they
        # don't act as a stand-in member on these two endpoints.
        if self.action == "create":
            return [
                permissions.IsAuthenticated(),
                IsMember(),
            ]

        if self.action == "return_book":
            return [
                permissions.IsAuthenticated(),
                IsMember(),
                IsLoanOwnerOrAdmin(),
            ]

        if self.action in [
            "retrieve",
        ]:
            return [
                permissions.IsAuthenticated(),
                IsLoanOwnerOrAdmin(),
            ]

        return [
            permissions.IsAuthenticated(),
        ]