import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.pretty import pretty_repr

from src.preprocessing.schema import read_yaml

logger = logging.getLogger('DT_logger')


class GeneralPurposeManager:
    """
    Generic handler of the Digital Twin experiment.
    -----------------------------------------
    The simulator is conceived to be the orchestrator and the brain of the specified experiment.

    From here, all the kinds of data (input, output, config) are delivered to their consumer hubs, the
    environment is instantiated and the instructions related to the simulation mode chosen by the user are provided.
    """
    @classmethod
    def get_instance(cls, mode: str):
        """
        Get the instance of the subclass for the current experiment mode, checking if the mode name is
        contained inside the subclass name.
        NOTE: this works because of the __init__.py, otherwise the method __subclasses__() cannot find
              subclasses in other not yet loaded modules.
        """
        logger.info("Starting '{}' experiment...".format(mode))
        return next(c for c in cls.__subclasses__() if mode in c.__name__.lower())

    def __init__(self,
                 config_folder: str,
                 output_folder: str,
                 ground_folder: str,
                 exp_id_folder: str,
                 assets_file: str,
                 models: list,
                 save_results: bool,
                 plot_results: bool,
                 ):
        """
        Args:
            config_folder (str):
            output_folder (str):
            ground_folder (str):
            exp_id_folder (str):
            assets_file (str):
            models (list): models to instantiate for the current experiment, given in input by the user
            save_results (bool):
            plot_results (bool):
        """
        # Store paths for all different kind of preprocessing
        self._config_folder = Path(config_folder)
        self._ground_folder = Path(ground_folder)
        self._assets = read_yaml(yaml_file=assets_file, yaml_type="assets")
        self._output_folder = Path(output_folder) / exp_id_folder / str(datetime.now().strftime('%Y_%m_%d-%H_%M'))

        # Get models config files
        self._models_configs = []
        for model in models:
            model_file = (Path(self._assets['models_path']) / self._assets['models'][model]['category'] /
                          self._assets['models'][model]['file'])
            self._models_configs.append(self._config_folder / model_file)

        # Output results and visualization
        self._save_results = save_results
        self._plot_results = plot_results

    def run(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def _save_plots(self):
        pass

    def _output_results(self, results: pd.DataFrame, summary: dict):
        """


        Args:
            summary ():

        """
        if self._save_results:
            try:
                os.makedirs(self._output_folder, exist_ok=True)
            except NotADirectoryError as e:
                logger.error("It's not possible to create directory {}: {}".format(self._output_folder, e.args))

            # Save experiment summary
            with open(self._output_folder / "summary.txt", 'w') as f:
                for key, value in summary.items():
                    f.write('%s: %s\n' % (key, value))

            # Save experiment results
            results.to_csv(self._output_folder / 'dataset.csv', index=False)
        else:
            # Print on the console the summary and results
            print(pretty_repr(summary))
            print('\n' + str(results))




