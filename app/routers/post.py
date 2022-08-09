from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..schemas import Post, PostCreate, PostOut
from ..database import get_db
from .. import models, oauth2


router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)


# @router.get('/', response_model=List[Post])
@router.get('/', response_model=List[PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # """ Using SQL """
    # cursor.execute(""" SELECT * FROM posts """)
    # posts = cursor.fetchall()

    # """ Using Sqlalchemy """
    # posts = db.query(models.Post).filter(
    #     models.Post.title.contains(search)).limit(limit).offset(skip).all()

    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(
        models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=Post)
def create_posts(post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # """ Using Python List """
    # post_dict = post.dict()
    # post_dict['id'] = randrange(0,1000000)
    # all_posts.routerend(post_dict)

    # """ Using SQL """
    # cursor.execute(""" INSERT INTO posts (title, content, published) VALUES (%s,%s,%s) RETURNING * """,(post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()
    # return {"data":new_post}

    # """ Using SQLAlchemy """
    # new_posts = models.Post(
    #     title=post.title, content=post.content, published=post.published)
    # print(current_user.email)
    new_posts = models.Post(owner_id=current_user.id, **post.dict())
    db.add(new_posts)
    db.commit()
    db.refresh(new_posts)

    return new_posts


# @router.get('/posts/latest')
# def latest():
#     post = all_posts[len(all_posts)-1]
#     return {"data":post}


@router.get('/{id}', response_model=PostOut)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # single_post = find_post(id)

    # """ Using SQL """
    # cursor.execute(""" SELECT * FROM posts WHERE id = %s """, (str(id),))
    # single_post = cursor.fetchone()

    # """ Using SQLAlchemy """
    # single_post = db.query(models.Post).filter(models.Post.id == id).first()
    single_post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.id == id).first()

    if not single_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {id} Not Found!!")
    # response.status_code = status.HTTP_404_NOT_FOUND
    # return {"message":f"Post with id {id} Not Found!!"}
    return single_post


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # """ Using SQL """
    # cursor.execute(
    #     """ DELETE FROM posts WHERE id = %s RETURNING * """, (str(id), ))
    # deleted_post = cursor.fetchone()
    # conn.commit()
    # index = find_index_post(id)

    # """ Using SQLAlchemy """
    deleted_post = db.query(models.Post).filter(models.Post.id == id)

    if deleted_post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {id} does not exist")
    # all_posts.pop(index)
    if deleted_post.first().owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    deleted_post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=Post)
def update(id: int, post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # """ Using SQL """
    # cursor.execute(""" UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
    #                (post.title, post.content, post.published, str(id)))
    # updated_post = cursor.fetchone()
    # conn.commit()
    # index = find_index_post(id)

    # """ Using SQLAlchemy """
    post_query = db.query(models.Post).filter(models.Post.id == id)
    updated_post = post_query.first()

    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {id} does not exist")

    if updated_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    updated_post = post_query.update(post.dict(), synchronize_session=False)

    db.commit()
    # post_dict = post.dict()
    # post_dict['id'] = id
    # all_posts[index] = post_dict
    return post_query.first()
