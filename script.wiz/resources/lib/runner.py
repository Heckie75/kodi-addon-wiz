import xbmc


class WizRunner(xbmc.Monitor):
    """Monitor and Player class for WiZ Control addon."""

    def __init__(self):
        """Initialize the WizRunner monitor and player."""
        xbmc.Monitor.__init__(self)

    def start(self):
        """Start the main monitoring loop."""
        while not self.abortRequested():
            # Main event loop
            if self.waitForAbort(1):
                break

    def onDatabaseUpdate(self, database):
        """Handle database update event.

        Args:
            database: The database that was updated
        """
        pass

    def onNotification(self, sender, method, data):
        """Handle notification event.

        Args:
            sender: The sender of the notification
            method: The notification method
            data: The notification data
        """
        pass

    def onSettingsChanged(self):
        """Handle settings changed event."""
        pass

    def onScreensaverActivated(self):
        """Handle screensaver activated event."""
        pass

    def onScreensaverDeactivated(self):
        """Handle screensaver deactivated event."""
        pass
