===========
構築フロー
===========

OASEの環境構築、インストール手順の流れを説明します。
環境構築、インストール作業の所要時間は、15分程度を見込んでください。

.. blockdiag::
   :align: center

   blockdiag {
      orientation = portrait;
      plugin autoclass;
      OS環境設定 -> python関連 -> Django関連 -> MariaDB関連 -> Apache関連 -> Java関連 -> RedHad関連 -> Mavenインストール -> 動作確認;
   }
