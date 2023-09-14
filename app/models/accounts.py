from . import *


class Accounts(db.Model, MetaMixins):
    account_id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    salt = db.Column(db.String(4), nullable=False)
    disabled = db.Column(db.Boolean)

    rel_roles = relationship(
        "RolesMembership",
        order_by="RolesMembership.fk_role_id",
        primaryjoin="Accounts.account_id==RolesMembership.fk_account_id",
        viewonly=True,
    )

    rel_profile = relationship(
        "Profile",
        order_by="Profile.profile_id",
        primaryjoin="Accounts.account_id==Profile.fk_account_id",
        viewonly=True,
    )

    @classmethod
    def exists(cls, email_address):
        return db.session.execute(
            select(cls.account_id).filter_by(email_address=email_address).limit(1)
        ).scalar_one_or_none()

    @classmethod
    def get_roles_from_email_address_select(cls, email_address):
        result = db.session.execute(
            select(cls).filter_by(email_address=email_address).limit(1)
        ).scalar_one_or_none()
        return [role.rel_role.name for role in result.rel_roles]

    def get_roles_from_this(self):
        return [role.rel_role.name for role in self.rel_roles]

    @classmethod
    def select_all(cls):
        return db.session.execute(
            select(cls).order_by(cls.email_address)
        ).scalars().all()

    @classmethod
    def select_using_id(cls, account_id):
        return db.session.execute(
            select(cls).filter_by(account_id=account_id).limit(1)
        ).scalar_one_or_none()

    @classmethod
    def select_using_email_address(cls, email_address):
        return db.session.execute(
            select(cls).filter_by(email_address=email_address).limit(1)
        ).scalar_one_or_none()

    @classmethod
    def select_account_id_using_email_address(cls, email_address):
        return db.session.execute(
            select(cls.account_id).filter_by(email_address=email_address).limit(1)
        ).scalar_one_or_none()

    @classmethod
    def create(cls, email_address, password, disabled):
        """
        Written for sqlite. Returns primary key after creation.
        """
        from flask_imp.auth import Auth

        salt = Auth.generate_salt()
        salt_and_pepper_password = Auth.hash_password(password, salt)

        db.session.execute(
            insert(cls).values(
                email_address=email_address,
                password=salt_and_pepper_password,
                salt=salt,
                disabled=disabled,
            )
        )
        db.session.commit()

        return cls.get_by_email_address(email_address).account_id

    @classmethod
    def update(
            cls,
            account_id: int,
            email_address: str,
            disabled: bool
    ):
        db.session.execute(
            update(cls).where(
                cls.account_id == account_id
            ).values(
                email_address=email_address,
                disabled=disabled,
            )
        )
        db.session.commit()

    @classmethod
    def reset_password(
            cls,
            account_id: int,
            new_password: str,
    ):
        from flask_imp.auth import Auth

        salt = Auth.generate_salt()
        salt_and_pepper_password = Auth.hash_password(new_password, salt)

        db.session.execute(
            update(cls).where(
                cls.account_id == account_id
            ).values(
                password=salt_and_pepper_password,
                salt=salt,
            )
        )
        db.session.commit()

    @classmethod
    def delete(cls, account_id: int):
        db.session.execute(
            delete(cls).where(
                cls.account_id == account_id
            )
        )
        db.session.commit()

    # batch actions:

    @classmethod
    def create_batch(cls, batch: list[dict]):
        """
        batch: [{"email_address": -, "password": -, "disabled": -}]
        :param batch:
        :return:
        """

        from flask_imp.auth import Auth

        for value in batch:
            salt = Auth.generate_salt()
            salt_and_pepper_password = Auth.hash_password(value.get("password", "password"), salt)

            db.session.execute(
                insert(cls).values(
                    email_address=value.get("email_address", "null@null.null"),
                    password=salt_and_pepper_password,
                    salt=salt,
                    disabled=value.get("disabled", False),
                )
            )

        db.session.commit()

    @classmethod
    def get_account_ids_from_email_address_select_batch(cls, email_addresses: list[str]) -> list[int]:
        return db.session.execute(
            select(cls.account_id).where(cls.email_address.in_(email_addresses))
        ).scalars().all()
