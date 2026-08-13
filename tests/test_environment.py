from videoforge.engine.environment import detect_environment

env = detect_environment()

print(env.model_dump_json(indent=4))
