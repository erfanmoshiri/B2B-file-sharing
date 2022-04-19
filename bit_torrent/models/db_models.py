from django.db import models

default_app_config = 'bit_torrent.apps.BitTorrentConfig'


class DbPeer(models.Model):
    name = models.CharField(
        max_length=64,
    )
    port = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'bit_torrent'

    def deactivate(self):
        self.is_active = False
        self.save()

    def activate(self):
        self.is_active = True
        self.save()

class DbFile(models.Model):
    name = models.CharField(max_length=64)
    peers = models.ManyToManyField(
        to='bit_torrent.DbPeer',
        related_name='files',
    )


class DbTransaction(models.Model):
    sender = models.ForeignKey(
        to='bit_torrent.DbPeer',
        related_name='send_transactions',
        on_delete=models.SET_NULL,
        null=True
    )
    receiver = models.ForeignKey(
        to='bit_torrent.DbPeer',
        related_name='recv_transactions',
        on_delete=models.SET_NULL,
        null=True
    )
