import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Callable, Coroutine, Any

import requests as requests
import bs4
from sqlalchemy import select
from telegram.ext import JobQueue, ContextTypes

from src import db_session
from src.config import free_subscription
from src.items import Item
from src.tasks import Task
from src.users import User


logger = logging.getLogger("store_keeper")


class StoreKeeper:
    def __init__(self, job_queue: JobQueue,
                 notification: Callable[[ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]],
                 subscription_end: Callable[[ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]):
        db_session.global_init(Path().resolve() / "res/db/bina_data.sqlite")
        users = self.get_all_active_users()
        now = datetime.now()
        for user in users:
            job_queue.run_once(subscription_end, datetime.fromtimestamp(user.subscription_till) - now,
                               name=f"sub{user.id}", user_id=user.id)
        user_ids = list(map(lambda x: x.id, users))
        tasks = self.get_all_tasks()
        for task in tasks:
            if task.id not in user_ids:
                continue
            job_queue.run_repeating(notification, task.frequency * 60, name=str(task.id), user_id=task.user_id)
        logger.debug("Initialized store keeper")

    @staticmethod
    def new_user(user_id: int) -> datetime:
        session = db_session.create_session()
        user = session.execute(select(User).where(User.id == user_id)).scalar()
        if user:
            session.close()
            raise KeyError("User already exists")
        user = User()
        user.id = user_id
        subscription_till = datetime.now() + timedelta(free_subscription)
        user.subscription_till = subscription_till.timestamp()
        session.add(user)
        session.commit()
        session.close()
        return subscription_till

    @staticmethod
    def get_all_active_users() -> List[User]:
        now = datetime.now().timestamp()
        session = db_session.create_session()
        users = session.execute(select(User).where(User.subscription_till > now)).scalars().all()
        session.close()
        return list(users)

    @staticmethod
    def add_subscription_time(user_id: int, days: int) -> datetime:
        session = db_session.create_session()
        user = session.execute(select(User).where(User.id == user_id)).scalar()
        if not user:
            session.close()
            raise KeyError("No such user")
        subscription_till = max(datetime.fromtimestamp(user.subscription_till), datetime.now()) + timedelta(days)
        user.subscription_till = subscription_till.timestamp()
        session.commit()
        session.close()
        return subscription_till

    @staticmethod
    def get_subscription_time(user_id: int) -> datetime:
        session = db_session.create_session()
        user = session.execute(select(User).where(User.id == user_id)).scalar()
        session.close()
        if not user:
            raise KeyError("No such user")
        subscription_till = datetime.fromtimestamp(user.subscription_till)
        return subscription_till

    def add_task(self, user_id: int, name: str, url: str, frequency: int) -> int:
        logger.debug("Adding task")
        items = self.get_last_k_items(url)
        if not items:
            raise KeyError("No items")
        session = db_session.create_session()
        task = Task()
        task.user_id = user_id
        task.name = name
        task.url = url
        task.frequency = frequency
        task.last_items = ';'.join(map(lambda x: str(x.id), items))
        session.add(task)
        session.commit()
        session.close()
        return task.id

    @staticmethod
    def get_tasks(user_id: int) -> List[Task]:
        session = db_session.create_session()
        tasks = session.execute(select(Task).where(Task.user_id == user_id)).scalars().all()
        session.close()
        return list(tasks)

    @staticmethod
    def get_all_tasks() -> List[Task]:
        session = db_session.create_session()
        tasks = session.execute(select(Task)).scalars().all()
        session.close()
        return list(tasks)

    @staticmethod
    def get_task(task_id: int) -> Task | None:
        session = db_session.create_session()
        task = session.execute(select(Task).where(Task.id == task_id)).scalar()
        session.close()
        return task

    @staticmethod
    def remove_task(task_id: int) -> None:
        session = db_session.create_session()
        task = session.execute(select(Task).where(Task.id == task_id)).scalar()
        if not task:
            session.close()
            return
        session.delete(task)
        session.commit()
        session.close()

    @staticmethod
    def get_last_k_items(url: str, number_of_items: int = 50) -> List[Item] | None:
        if "bina.az" not in url:
            raise KeyError()
        params = dict()
        try:
            link, _, params_str = url.partition('?')
            for param in params_str.split('&'):
                key, value = param.split('=')
                params[key] = value
        except ValueError:
            link = url
        params['sorting'] = 'bumped_at+desc'
        params['items_view'] = 'list'
        params['page'] = 1
        url = link + '?' + '&'.join([key + '=' + str(value) for key, value in params.items()])
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
            }
        )
        soup = bs4.BeautifulSoup(r.text, features="html.parser")
        data = soup.find_all("div", {"class": "items-i"}, limit=number_of_items + 4)[4:]
        if not data:
            return None
        items = []
        for page in data:
            price = page.find("div", class_="price").text.strip()
            place = page.find("div", class_="location").text.strip()
            id = int(page.find("a", class_="item_link")['href'].split('/')[-1])
            items.append(Item(id, price, place))
        return items[:number_of_items]

    def get_new_items(self, task_id: int) -> List[Item] | None:
        session = db_session.create_session()
        task = session.execute(select(Task).where(Task.id == task_id)).scalar()
        if task is None:
            session.close()
            return None
        previous_item_ids = list(map(int, task.last_items.split(';')))
        last_items = self.get_last_k_items(task.url)
        if not last_items:
            session.close()
            return None
        new_items = []
        for item in last_items:
            if item.id in previous_item_ids:
                break
            new_items.append(item)
        if not new_items:
            session.close()
            return None
        task.last_items = ';'.join(map(lambda x: str(x.id), last_items))
        session.commit()
        session.close()
        return new_items
