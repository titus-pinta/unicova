<?php

// autoload_static.php @generated by Composer

namespace Composer\Autoload;

class ComposerStaticInit3bf12969f22cfa192db5ecf86d6f5f89
{
    public static $prefixLengthsPsr4 = array (
        'a' => 
        array (
            'atk4\\dsql\\' => 10,
            'atk4\\core\\' => 10,
        ),
        'P' => 
        array (
            'Psr\\Log\\' => 8,
        ),
    );

    public static $prefixDirsPsr4 = array (
        'atk4\\dsql\\' => 
        array (
            0 => __DIR__ . '/..' . '/atk4/dsql/src',
        ),
        'atk4\\core\\' => 
        array (
            0 => __DIR__ . '/..' . '/atk4/core/src',
        ),
        'Psr\\Log\\' => 
        array (
            0 => __DIR__ . '/..' . '/psr/log/Psr/Log',
        ),
    );

    public static function getInitializer(ClassLoader $loader)
    {
        return \Closure::bind(function () use ($loader) {
            $loader->prefixLengthsPsr4 = ComposerStaticInit3bf12969f22cfa192db5ecf86d6f5f89::$prefixLengthsPsr4;
            $loader->prefixDirsPsr4 = ComposerStaticInit3bf12969f22cfa192db5ecf86d6f5f89::$prefixDirsPsr4;

        }, null, ClassLoader::class);
    }
}
