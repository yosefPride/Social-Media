import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.database import comment_table, database, like_table, post_table
from app.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from app.models.user import User
from app.security import get_current_user
from app.tasks import generate_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)

select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post_by_id(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)

    logger.info(f"Finding post with id {post_id}")
    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/posts", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str = None,
):
    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(data)

    logger.info("Creating a post")
    logger.debug(query)

    last_record_id = await database.execute(query)

    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            request.url_for("get_post_with_comments", post_id=last_record_id),
            database,
            prompt,
        )

    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/posts", response_model=list[UserPostWithLikes])
async def get_all_posts(
    sorting: PostSorting = PostSorting.new,
):  # allows for http://api.com/post?sorting=most_likes
    match sorting:
        case PostSorting.new:
            query = select_post_and_likes.order_by(post_table.c.id.desc())
        case PostSorting.old:
            query = select_post_and_likes.order_by(post_table.c.id.asc())
        case PostSorting.most_likes:
            query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.info("Getting all posts")
    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comments", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    post = await find_post_by_id(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**comment.model_dump(), "user_id": current_user.id}
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
    query = select_post_and_likes.where(post_table.c.id == post_id)

    logger.info("Getting a post with comments")
    logger.debug(query)

    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post": post,
        "comments": await get_all_comments(post_id),
    }


@router.post("/likes", response_model=PostLike, status_code=201)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    post = await find_post_by_id(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)

    logger.info("Liking a post")
    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
