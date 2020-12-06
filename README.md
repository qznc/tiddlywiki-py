# Simple TiddlyWiki Server

For Ubuntu, copy the tiddle.service and enable it.

    cp tiddle.service ~/.local/share/systemd/user/tiddle.service
    systemctl --user enable tiddle
    systemctl --user start tiddle
