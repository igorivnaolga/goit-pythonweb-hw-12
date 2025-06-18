import cloudinary
import cloudinary.uploader


class UploadFileService:
    def __init__(self, cloud_name, api_key, api_secret):
        """
        Constructor for the UploadFileService class.

        Args:
            cloud_name (str): Cloudinary cloud name.
            api_key (str): Cloudinary API key.
            api_secret (str): Cloudinary API secret.

        Initializes the Cloudinary client with the given cloud name, API key, and API secret.

        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Uploads a file to Cloudinary and returns the URL of the uploaded image.

        Args:
            file (UploadFile): The file to be uploaded.
            username (str): The username of the user to whom the uploaded image belongs.

        Returns:
            str: The URL of the uploaded image.

        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
