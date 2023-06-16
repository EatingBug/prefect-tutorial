from datetime import datetime
from typing import List

import mlflow
import pandas as pd
import prefect
from prefect import task
from sqlalchemy import create_engine
from sklearn.pipeline import Pipeline

from utils import save_prediction

logger = prefect.context.get("logger")


@task(log_stdout=True)
def load_test_data() -> pd.DataFrame:
    logger.info("Data Preprocessing start")
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")

    sql = "SELECT * FROM public.apartments where transaction_real_price is null"
    test  = pd.read_sql(sql, con=engine)

    test.drop(columns=['apartment_id', 'transaction_id', 'transaction_real_price', 'jibun', 'apt', 'addr_kr', 'dong'], axis=1, inplace=True)

    return test


@task(log_stdout=True)
def load_model_task(model_name: str) -> Pipeline:
    logger.info("Load Production Model Start.")

    model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

    logger.info("Done Load Model.")

    return model


@task(log_stdout=True, nout=2)
def batch_inference_task(
    model: Pipeline,
    data: pd.DataFrame,
) -> List[pd.DataFrame]:
    logger.info("Batch Inference Start")

    results = pd.read_csv("submission.csv")
    results["transaction_real_price"] = model.predict(data)
    results["predict_date"] = datetime.now().date()

    logger.info("Batch Inference Done")
    return results


@task(log_stdout=True)
def save_database(results: List[pd.DataFrame]) -> None:
    logger.info("Save to db Start")

    save_prediction(results)

    logger.info("Save Result Done")
