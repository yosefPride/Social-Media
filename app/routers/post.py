import logging

from fastapi import APIRouter, HTTPException, Request

from app.database import comment_table, database, post_table
from app.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from app.models.user import User
from app.security import Oauth2_scheme, get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post_by_id(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)

    logger.info(f"Finding post with id {post_id}")
    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/posts", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn, request: Request):
    current_user: User = await get_current_user(await Oauth2_scheme(request))  # noqa

    data = post.model_dump()
    query = post_table.insert().values(data)

    logger.info("Creating a post")
    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/posts", response_model=list[UserPost])
async def get_all_posts():
    query = post_table.select()

    logger.info("Getting all posts")
    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comments", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn, request: Request):
    current_user: User = await get_current_user(await Oauth2_scheme(request))  # noqa

    post = await find_post_by_id(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = comment.dict()
    query = comment_table.insert().values(data)

    logger.info("Creating a comment")
    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/posts/{post_id}/comments", response_model=list[Comment])
async def get_all_comments(post_id: int):
    query = comment_table.select().where(comment_table.c.post_id == post_id)

    logger.info("getting all comments on a post")
    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/posts/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting a post with comments")

    post = await find_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post": post,
        "comments": await get_all_comments(post_id),
    }
