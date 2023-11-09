import pandas as pd
import logging
from tqdm import tqdm

from src.digital_twin.handlers.base_manager import GeneralPurposeManager
from src.digital_twin.bess import BatteryEnergyStorageSystem
from src.visualization.fast_plots import plot_compared_data
from src.preprocessing.data_preparation import load_data_from_csv, validate_parameters_unit
from src.preprocessing.schema import read_yaml

logger = logging.getLogger('DT_logger')


class SimulationManager(GeneralPurposeManager):
    """

    """
    def __init__(self, **kwargs):
        self._mode = "simulation"
        logger.info("Instantiated {} class as experiment orchestrator".format(self.__class__.__name__))

        self._settings = read_yaml(yaml_file=kwargs['config'], yaml_type='sim_config')

        super().__init__(config_folder=kwargs['config_folder'],
                         output_folder=kwargs['output_folder'],
                         ground_folder=kwargs['ground_folder'],
                         exp_id_folder=self._mode + '/' + self._settings['destination_folder'],
                         assets_file=kwargs['assets'],
                         models=kwargs['models'],
                         save_results=kwargs['save_results'],
                         plot_results=kwargs['plot'],
                         )

        # Prepare ground preprocessing for input and validation
        self._input_var = self._settings['ground_data']['load']
        self._ground_data, self._ground_times = (
            load_data_from_csv(csv_file=self._ground_folder / self._settings['ground_data']['file'],
                               vars_to_retrieve=self._settings['ground_data']['vars'],
                               iterations=None)
        )

        # Time options
        self._duration = self._ground_times[-1] - self._ground_times[0]
        self._elapsed_time = 0
        #TODO: understand if DONE mi serve
        self.done = False

        # Validate battery parameters unit
        self._settings['battery']['params'] = validate_parameters_unit(self._settings['battery']['params'])

        # Instantiate the BESS environment
        self._battery = BatteryEnergyStorageSystem(
            models_config_files=self._models_configs,
            battery_options=self._settings['battery'],
            input_var=self._input_var
        )

    def run(self):
        """
        Simulation experiment:

        """
        logger.info("'Simulation' started...")
        self._battery.reset_data()
        self._battery.simulation_init()

        load = self._ground_data[self._input_var].copy()
        times = self._ground_times.copy()

        k = 0
        dt = 1
        pbar = tqdm(total=int(self._duration), position=0, leave=True)

        # Main loop of the simulation
        while self._elapsed_time < self._duration:
            # No progress in the simulation due to preprocessing timestamp
            if dt == 0:
                load.pop(k)
                times.pop(k)
            else:
                self._battery.simulation_step(load=load[k], dt=dt, k=k - 1)
                self._battery.t_series.append(self._elapsed_time)
                self._elapsed_time += dt
                k += 1

            pbar.update(dt)
            dt = times[k] - times[k - 1]

        pbar.close()
        logger.info("'Simulation' ended without errors!")
        self.done = True
        self._output_results(results=self._battery.build_results_table(), summary=self._get_summary())

    def _get_summary(self):
        """
        Get simulation summary with important information
        TODO: update when will be added new features
        """
        return {'experiment': self._settings['experiment_name'],
                'description': self._settings['description'],
                'goal': self._settings['goal'],
                'load': self._settings['ground_data']['load'],
                'time': self._elapsed_time,
                'battery': self._settings['battery']['params'],
                'initial_conditions': self._settings['battery']['init'],
                'models': [model.__class__.__name__ for model in self._battery.models]
                }

    def _show_results(self):
        """
        """
        if self._plot_results:
            var_to_plot = ['Voltage [V]', 'Temperature [degC]', 'Power [W]']
            self._fast_plot(var_to_plot=var_to_plot)

    def _fast_plot(self, var_to_plot: list):
        """
        # TODO: clean up this method -> add save plot img option
        """
        df = self._battery.build_results_table()
        # print(df['Power [W]'])

        df_ground = pd.read_csv(self.ground_data_path / self.experiment_config['ground_data']['file'], encoding='unicode_escape')
        if self._iterations:
            df_ground = df_ground.iloc[:self._iterations]

        df_ground['Timestamp'] = pd.to_datetime(df_ground['Time'], format="%Y/%m/%d %H:%M:%S").values.astype(
            float) // 10 ** 9
        df_ground['Timestamp'] = df_ground['Timestamp'] - df_ground['Timestamp'][0]

        for var in var_to_plot:
            dfs = [df.iloc[1:], df_ground]
            var = [var, var]
            labels = ['Simulated', 'Ground']
            x_axes = ['Time', 'Timestamp']
            title = var

            plot_compared_data(dfs=dfs, variables=var, x_axes=x_axes, labels=labels, title=title)