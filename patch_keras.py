
import os
target_file = "/home/sebabte/cancer/lib/python3.12/site-packages/keras/src/saving/keras_saveable.py"

new_content = """import io

class KerasSaveable:
    # Note: renaming this function will cause old pickles to be broken.

    def _obj_type(self):
        raise NotImplementedError(
            "KerasSaveable subclases must provide an "
            "implementation for `obj_type()`"
        )

    @classmethod
    def _unpickle_model(cls, bytesio):
        from keras.src.saving import saving_lib
        print(f"DEBUG: saving_lib type: {type(saving_lib)}")
        
        # pickle is not safe regardless of what you do.
        return saving_lib._load_model_from_fileobj(
            bytesio, custom_objects=None, compile=True, safe_mode=False
        )

    def __reduce__(self):
        from keras.src.saving import saving_lib

        buf = io.BytesIO()
        saving_lib._save_model_to_fileobj(self, buf, "h5")
        return (
            self._unpickle_model,
            (buf,),
        )
"""

with open(target_file, "w") as f:
    f.write(new_content)

print("Patched keras_saveable.py")
