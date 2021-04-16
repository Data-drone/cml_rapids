## Feature Engineering cu-dask

import time

from dask.distributed import Client, wait
from dask_cuda import LocalCUDACluster
import dask_cudf
import numpy as np

cluster = LocalCUDACluster()
client = Client(cluster)
client

### Load Data
bureau_balance = dask_cudf.read_csv('data/bureau_balance.csv')
bureau = dask_cudf.read_csv('data/bureau.csv')
cc_balance = dask_cudf.read_csv('data/credit_card_balance.csv')
payments = dask_cudf.read_csv('data/installments_payments.csv')
pc_balance = dask_cudf.read_csv('data/POS_CASH_balance.csv')
prev = dask_cudf.read_csv('data/previous_application.csv')
train = dask_cudf.read_csv('data/application_train.csv')
test = dask_cudf.read_csv('data/application_test.csv')

## aggregation functions for our groupings
agg_func = ['mean', 'max', 'min', 'sum', 'std']

## Build Average Bureau Balance
avg_bbalance = bureau_balance.select_dtypes('number') \
                .groupby('SK_ID_BUREAU').agg(agg_func)

avg_bbalance.columns = ["_".join(x) for x in avg_bbalance.columns.ravel()]

## Build sum Credit Card Balance
sum_cc_balance = cc_balance.drop('SK_ID_PREV', axis=1) \
                    .select_dtypes('number').groupby('SK_ID_CURR') \
                    .agg(agg_func)

sum_cc_balance.columns = ["_".join(x) for x in sum_cc_balance.columns.ravel()]

## Build Avg Bureau table
avg_bureau = bureau.merge(avg_bbalance, how='left', 
                          left_on='SK_ID_BUREAU', 
                          right_index=True)

## Buld Payments
sum_payments = payments.drop('SK_ID_PREV', axis=1)
sum_payments['PAYMENT_PERC'] = sum_payments.AMT_PAYMENT / sum_payments.AMT_INSTALMENT
sum_payments['PAYMENT_DIFF'] = sum_payments.AMT_INSTALMENT - sum_payments.AMT_PAYMENT
sum_payments['DPD'] = sum_payments.DAYS_ENTRY_PAYMENT - sum_payments.DAYS_INSTALMENT
sum_payments['DBD'] = sum_payments.DAYS_INSTALMENT - sum_payments.DAYS_ENTRY_PAYMENT
sum_payments['DPD'] = sum_payments['DPD']
sum_payments['DBD'] = sum_payments['DBD']

## Build Sum_PC_Balance
sum_pc_balance = pc_balance.drop('SK_ID_PREV', axis=1).select_dtypes('number').groupby('SK_ID_CURR') \
            .agg(agg_func)

sum_pc_balance.columns = ["_".join(x) for x in sum_pc_balance.columns.ravel()]

## Build Sum_Prev
prev = prev.drop('SK_ID_PREV', axis=1)
prev.DAYS_FIRST_DRAWING = prev.DAYS_FIRST_DRAWING.map(lambda x: np.nan if x == 365243 else x)
prev.DAYS_FIRST_DUE = prev.DAYS_FIRST_DUE.map(lambda x: np.nan if x == 365243 else x)
prev.DAYS_LAST_DUE_1ST_VERSION = prev.DAYS_LAST_DUE_1ST_VERSION.map(lambda x: np.nan if x == 365243 else x)
prev.DAYS_LAST_DUE = prev.DAYS_LAST_DUE.map(lambda x: np.nan if x == 365243 else x)
prev.DAYS_TERMINATION = prev.DAYS_TERMINATION.map(lambda x: np.nan if x == 365243 else x)
prev.APP_CREDIT_PERC = prev.AMT_APPLICATION / prev.AMT_CREDIT

sum_prev = prev.select_dtypes('number').groupby('SK_ID_CURR') \
            .agg(agg_func)

sum_prev.columns = ["_".join(x) for x in sum_prev.columns.ravel()]


## Outputs - to write out
## Interesting... this creates a folder then a file in each
avg_bureau.to_parquet(path='data_eng/avg_bureau')
sum_cc_balance.to_parquet(path='data_eng/sum_cc_balance')
sum_payments.to_parquet(path='data_eng/sum_payments')
sum_pc_balance.to_parquet(path='data_eng/sum_pc_balance')
sum_prev.to_parquet(path='data_eng/sum_prev')

## we still ran out of memory

