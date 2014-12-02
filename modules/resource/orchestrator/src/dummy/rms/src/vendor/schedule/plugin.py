from amsoil.core import pluginmanager as pm

def setup():
    config = pm.getService("config")
    config.install("schedule.dbpath", "deploy/schedule.db", "Path to the schedule database (if relative, AMsoil's root will be assumed as base).")

    from schedulep import Schedule
    pm.registerService('schedule', Schedule)
    import scheduleexceptions as exceptions_package
    pm.registerService('scheduleexceptions', exceptions_package)
