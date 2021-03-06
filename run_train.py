# Config
from config import config as cfg
# Controllers
from dlframework.unwrappers.general_unwrappers import unwrapper
from dlframework.filters.general_filters import threshold_ignore_label, threshold_accept_label
# Dl Framework
from dlframework.retrievals.MySQL import MySQL
from dlframework.utils import get_logger
from dlframework.trainer.solver import train_model
from dlframework.datasource.planet_ds import PlanetDataSource
from dlframework.callbacks.classification_callbacks import recall_per_class, precision_per_class
from dlframework.nets.planet_nets import planet_structure_lrcn as net
## Other
import logging
import pandas as pd 
from functools import partial
import matplotlib
matplotlib.use('Agg')


#### Start Logger
logger = get_logger()
logger.setLevel(logging.INFO)

ds_params_val = {"local_cache_directory":cfg.local_cache_directory,
                             "batch_size":10,
                             "n_workers":1, 
                             "next_sample_timeout":1,
                             "processors":cfg.processors,
                             "unwrapper": [unwrapper]}

ds_params_train = ds_params_val.copy()
ds_params_train.update({"augmentors": cfg.augmentors, 
                        "batch_size": 1
                        })

testing = False
###############################
#######     K2 Data     #######
###############################
training_campaigns = None
validation_campaigns = None
names = []
if testing:
    training_campaigns = ['test_campaign']
    validation_campaigns = ['test_campaign']
    names = ['k2_test_planet', 'k2_test_other', 'k2_test_planet', 'k2_test_other']
else:
    training_campaigns = load_campaigns('Train_Campaigns.csv')
    validation_campaigns = load_campaigns('Validation_Campaigns.csv')
    names = ['k2_train_planet', 'k2_train_other', 'k2_val_planet', 'k2_val_other']

k2_trainds_planet = PlanetDataSource(datasource_name=names[0], dataset_name="original_k2_data",
                                    campaigns=training_campaigns,
                                    filters = cfg.filters + [is_planet],
                                    samplers = [planet_sampler], 
                                           **ds_params_train)

k2_trainds_other = PlanetDataSource(datasource_name=names[1], dataset_name="original_k2_data",
                                    campaigns=validation_campaigns,
                                    filters = cfg.filters + [is_other],
                                    samplers = [planet_sampler], 
                                           **ds_params_train)

#### VALIDATION DATASOURCE

k2_valds_planet = PlanetDataSource(datasource_name=names[2], dataset_name="original_k2_data",
                                    campaigns=training_campaigns,
                                    filters = cfg.filters + [is_planet],
                                    samplers = [planet_sampler], 
                                    **ds_params_val)

k2_valds_other = PlanetDataSource(datasource_name=names[3], dataset_name="original_k2_data",
                                    campaigns=validation_campaigns,
                                    filters = cfg.filters + [is_other],
                                    samplers = [planet_sampler], 
                                    **ds_params_val)

train_datasource =  k2_trainds_planet + k2_trainds_other
validation_datasource = k2_valds_planet + k2_valds_other




print '# of entities of Training dataset :', len(train_datasource.entities)
print '# of entities of Validation dataset :', len(validation_datasource.entities) 

def train(model, cwd, logger, experiment):
    train_model(model, train_datasource, validation_datasource, cfg)
    # serialize model to JSON
    model.save_model_to_json(cwd + 'models/' + experiment+".json")
    print 'Starting fit_generator'
    # serialize weights to HDF5
    model.save_model_h5(cwd + 'models/' + experiment +".h5")
    logger.info('Saved model to disk')    

def run_train(logger):
    # train_datasource.start_parallel_prefetch_loop()
    # validation_datasource.start_parallel_prefetch_loop()
    print 'building'
    print('Running', cfg.experiment_name, '...')
    model = net(num_classes = cfg.num_classes, input_shape = cfg.input_shape, transfer = cfg.transfer_learning)
    
    print 'model built, training'
    train(model, cfg.saving_path, logger, cfg.experiment_name)
    print 'finished training'
    
if __name__ == '__main__':
    run_train(logger)
