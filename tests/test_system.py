from videoforge.engine.system import system

print(system.model_dump())

print()

print("GPU Available:", system.gpu_available)
print("Best H264:", system.best_h264_encoder)
print("Best HEVC:", system.best_hevc_encoder)
