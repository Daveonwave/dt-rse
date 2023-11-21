import argparse
import os
import logging
from pathlib import Path
from src.digital_twin.handlers import GeneralPurposeManager


def get_args():
    main_parser = argparse.ArgumentParser(description="Digital Twin of a Battery Energy Storage System (RSE)",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    def get_sim_args():
        """
        Parser of arguments for SIMULATION mode
        """
        sim_parser.add_argument("--config", action="store", default="./data/config/sim_config.yaml",
                                type=str, help="Specifies the file containing parameters for simulation mode.")
        sim_parser.add_argument("--iterations", required=False, type=int,
                                help="Specifies the number of iterations of the simulation experiment.")

    def get_whatif_args():
        """
        Parser of arguments for WHAT-IF mode
        """
        whatif_parser.add_argument("--iterations", default=500, type=int,
                                   help="Specifies the number of iterations of the entire experiment.")
        whatif_parser.add_argument("--timestep", default=1., type=float,
                                   help="Specifies the timestep of the simulator in seconds.")

    def get_learn_args():
        """
        Parser of arguments for LEARNING mode
        """
        learn_parser.add_argument("--iterations", default=500, type=int,
                                  help="Specifies the number of iterations of the entire experiment.")
        learn_parser.add_argument("--timestep", default=1., type=float,
                                  help="Specifies the timestep of the simulator in seconds.")

    def get_optim_parser():
        """
        Parser of arguments for OPTIMIZATION mode
        """
        optim_parser.add_argument("--iterations", default=500, type=int,
                                  help="Specifies the number of iterations of the entire experiment.")
        optim_parser.add_argument("--timestep", default=1., type=float,
                                  help="Specifies the timestep of the simulator in seconds.")

    def get_generic_args():
        """
        Arguments of the main parser that can be useful to all the kind of modes
        """
        main_parser.add_argument("--config_folder", action="store", default="./data/config", type=str,
                                 help="Specifies the folder which we retrieve preprocessing from.")

        main_parser.add_argument("--output_folder", action="store", default="./data/output", type=str,
                                 help="Specifies the name of the folder where to store the output results.")

        main_parser.add_argument("--ground_folder", action="store", default="./data/ground", type=str,
                                 help="Specifies the folder which we retrieve preprocessing from.")

        main_parser.add_argument("--assets", action="store", default="./data/config/assets.yaml",
                                 type=str, help="Specifies the file containing parameters useful for the experiment.")

        electrical_choices = ['thevenin', 'data_driven']
        main_parser.add_argument("--battery_model", nargs=1, choices=electrical_choices, default=['thevenin'],
                                 help="Specifies the name of the core model of the battery, electrical or data driven.")

        thermal_choices = ['rc_thermal', 'r2c_thermal']
        main_parser.add_argument("--thermal_model", nargs=1, choices=thermal_choices, default=['rc_thermal'],
                                 help="Specifies the name of the thermal model that has to be used.")

        aging_choices = ['bolun']
        main_parser.add_argument("--aging_model", nargs=1, choices=aging_choices,
                                 help="Specifies the name of the aging model that has to be used.")

        main_parser.add_argument("--save_results", action="store_true",
                                 help="Specifies if save computed results at the end of the experiment.")

        main_parser.add_argument("--plot", action="store_true",
                                 help="Specifies if plot computed results at the end of the experiment.")

        main_parser.add_argument("--verbose", action="store_true",
                                 help="Increases logged information, but slows down the computation.")

    get_generic_args()
    subparsers = main_parser.add_subparsers(title="Mode", dest='mode', description="Experiment mode",
                                            help="Working mode of the Digital Twin", required=True)

    sim_parser = subparsers.add_parser('simulation', help="Simulation Mode",
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    get_sim_args()

    whatif_parser = subparsers.add_parser('whatif', help="What-If Mode",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    get_whatif_args()

    learn_parser = subparsers.add_parser('learning', help="Learning Mode",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    get_learn_args()

    optim_parser = subparsers.add_parser('optimization', help="Optimization Mode",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    get_optim_parser()

    main_args = vars(main_parser.parse_args())
    return main_args


if __name__ == '__main__':
    args = get_args()

    # Setup logger
    logging.basicConfig(format='%(asctime)s | %(name)s-%(levelname)s: %(message)s')
    logger = logging.getLogger(name="DT_logger")
    if args['verbose']:
        logger.setLevel(logging.INFO)

    # Parsing of models employed in the current experiment
    args['models'] = []
    if args['battery_model']:
        args['models'].extend(args['battery_model'])
        del args['battery_model']

    if args['thermal_model']:
        args['models'].extend(args['thermal_model'])
        del args['thermal_model']

    if args['aging_model']:
        args['models'].extend(args['aging_model'])
        del args['aging_model']

    dt_manager = GeneralPurposeManager.get_instance(args['mode'])
    handler = dt_manager(**args)
    handler.run()
