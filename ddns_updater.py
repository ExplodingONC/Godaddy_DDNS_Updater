from multiprocessing.pool import ThreadPool

from configs import config_list
from ddns_task import DDNSTask


if __name__ == "__main__":

    pool = ThreadPool(processes=len(config_list))
    task_list = []

    for ddns_config in config_list:
    
        api_config = ddns_config["api"]
        task_configs = ddns_config["task"]
        task = DDNSTask(api_config=api_config, task_configs=task_configs)
        task_list.append(task)

    pool.map(DDNSTask.run, task_list)

    pool.close()
    pool.join()
